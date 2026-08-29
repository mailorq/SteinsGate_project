import logging
import os
import secrets

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import Q
from PIL import Image

from .models import EmailVerificationCode

logger = logging.getLogger(__name__)

ALLOWED_EMAIL_DOMAINS = (
    "@gmail.com", "@yahoo.com", "@ukr.net", "@mail.ru",
    "@yandex.ru", "@outlook.com", "@icloud.com",
)
MAX_NICKNAME_LENGTH = 50
ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_AVATAR_SIZE = 8 * 1024 * 1024


class RegistrationError(Exception):
    pass


class VerificationError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


class ProfileError(Exception):
    pass


def _generate_code() -> str:
    return f"{secrets.randbelow(10 ** 6):06d}"


def _send_code_email(email: str, code: str) -> None:
    try:
        send_mail(
            subject="Verification Email",
            message=f"Your verification code is: {code}",
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as error:
        logger.exception("Verification email delivery failed")
        raise EmailDeliveryError(
            "Не удалось отправить письмо с кодом. Попробуйте позже."
        ) from error


def _consume_code(record, code: str, not_found_message: str) -> None:
    if record is None:
        raise VerificationError(not_found_message)

    if record.is_expired:
        raise VerificationError("Код истек. Запросите новый.")

    if record.attempts >= record.MAX_ATTEMPTS:
        raise VerificationError("Попытки исчерпаны. Запросите новый код.")

    record.attempts += 1
    record.save(update_fields=["attempts"])

    if not secrets.compare_digest(record.code, code):
        remaining = record.MAX_ATTEMPTS - record.attempts
        raise VerificationError(f"Неверный код. Осталось попыток: {remaining}")

    record.delete()


def _purge_stale_registration(*, username: str, email: str) -> None:
    candidates = User.objects.filter(is_active=False).filter(
        Q(username=username) | Q(email__iexact=email)
    )
    for user in candidates:
        record = EmailVerificationCode.objects.filter(user=user).first()
        if record is not None and record.is_expired:
            username = user.username
            user.delete()
            logger.info(f"Stale registration purged, username={username}")


def _validate_registration(*, username: str, email: str, password: str) -> None:
    try:
        UnicodeUsernameValidator()(username)
        validate_email(email)
    except DjangoValidationError as error:
        raise RegistrationError("; ".join(error.messages)) from None

    if not email.endswith(ALLOWED_EMAIL_DOMAINS):
        raise RegistrationError(
            "Допустимые домены почты: " + ", ".join(ALLOWED_EMAIL_DOMAINS)
        )
    if User.objects.filter(username=username).exists():
        raise RegistrationError("Имя пользователя уже занято")
    if User.objects.filter(email=email).exists():
        raise RegistrationError("Email уже используется")

    try:
        validate_password(password)
    except DjangoValidationError as error:
        raise RegistrationError("; ".join(error.messages)) from None


@transaction.atomic
def register_user(*, username: str, email: str, password: str) -> User:
    _purge_stale_registration(username=username, email=email)
    _validate_registration(username=username, email=email, password=password)

    try:
        user = User.objects.create_user(
            username=username, email=email, password=password, is_active=False
        )
    except IntegrityError:
        # параллельная регистрация успела занять username или email
        raise RegistrationError("Имя пользователя или email уже используется") from None
    code = _generate_code()
    EmailVerificationCode.objects.create(user=user, code=code)
    _send_code_email(email, code)
    logger.info("Verification email sent", extra={"user_email": email})
    return user


def verify_email(*, user: User, code: str) -> User:
    record = EmailVerificationCode.objects.filter(user=user).first()
    _consume_code(record, code, "Код не найден. Пройдите регистрацию заново.")

    user.is_active = True
    user.save(update_fields=["is_active"])
    return user


def authenticate_user(*, request, username: str, password: str) -> User | None:
    return authenticate(request, username=username, password=password)


def update_nickname(*, user: User, nickname: str) -> None:
    cleaned = nickname.strip()
    if not cleaned or len(cleaned) > MAX_NICKNAME_LENGTH:
        raise ProfileError(f"Никнейм должен быть от 1 до {MAX_NICKNAME_LENGTH} символов")

    user.profile.nickname = cleaned
    user.profile.save(update_fields=["nickname"])
    logger.debug(f"Nickname changed, user={user.username}")


def update_avatar(*, user: User, avatar) -> None:
    if avatar.size > MAX_AVATAR_SIZE:
        raise ProfileError("Файл слишком большой. Максимум 8 МБ")

    extension = os.path.splitext(avatar.name)[1].lower()
    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        raise ProfileError("Допустимые форматы: JPG, PNG, GIF, WEBP")

    # расширение подделывается тривиально, содержимое проверяет декодер
    # save(update_fields=...) не вызывает full_clean, валидаторы ImageField молчат
    try:
        Image.open(avatar).verify()
    except Exception:
        raise ProfileError("Файл не является изображением") from None
    finally:
        avatar.seek(0)

    profile = user.profile
    previous = profile.avatar.name
    profile.avatar = avatar
    profile.save(update_fields=["avatar"])

    # ImageField не удаляет прежний файл
    if previous and previous != profile.avatar.name:
        try:
            profile.avatar.storage.delete(previous)
        except OSError:
            logger.warning(f"Old avatar not removed, path={previous}")

    logger.debug(f"Avatar changed, user={user.username}")
