import logging
import os
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import IntegrityError, connection, transaction
from django.db.models import Q
from django.utils import timezone
from PIL import Image

from .models import EmailDeliveryQuota, EmailVerificationCode, email_delivery_fingerprint

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


class ResendCooldownError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Повторная отправка возможна через {retry_after} сек")


class ResendLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            "Лимит повторных отправок исчерпан. "
            f"Запросите новый код через {retry_after} сек"
        )


class EmailDeliveryLimitError(Exception):
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            "Для этого адреса достигнут лимит отправки кодов. "
            f"Попробуйте через {retry_after} сек"
        )


class ProfileError(Exception):
    pass


@dataclass(frozen=True)
class RegistrationResult:
    user: User
    delivered: bool
    delivery_scheduled: bool = False
    resend_available_in: int = 0


@dataclass(frozen=True)
class PurgeResult:
    registrations: int
    delivery_quotas: int


def _issue_code(record: EmailVerificationCode) -> str:
    issued_at = timezone.now()
    raw = record.rotate_code()
    record.attempts = 0
    record.created_at = issued_at
    record.last_sent_at = issued_at
    return raw


def _lock_or_create_email_delivery_quota(fingerprint: str) -> EmailDeliveryQuota:
    """Returns a row locked for this transaction, including first-use races."""
    while True:
        try:
            return EmailDeliveryQuota.objects.select_for_update().get(
                email_fingerprint=fingerprint
            )
        except EmailDeliveryQuota.DoesNotExist:
            try:
                with transaction.atomic():
                    return EmailDeliveryQuota.objects.create(email_fingerprint=fingerprint)
            except IntegrityError:
                continue


def _claim_email_delivery_quota(email: str) -> None:
    quota = _lock_or_create_email_delivery_quota(email_delivery_fingerprint(email))
    now = timezone.now()

    if quota.window_expired(now):
        quota.delivery_count = 0
        quota.window_started_at = now
    if quota.delivery_count >= quota.MAX_DELIVERIES:
        raise EmailDeliveryLimitError(max(quota.window_remaining(now), 1))

    quota.delivery_count += 1
    quota.save(update_fields=["delivery_count", "window_started_at"])


def _send_code_email(email: str, code: str) -> None:
    try:
        sent_count = send_mail(
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
    if sent_count != 1:
        logger.warning("Verification email was not accepted by the mail backend")
        raise EmailDeliveryError("Почтовый сервер не принял письмо")


def _deliver_code(email: str, code: str) -> bool:
    try:
        _send_code_email(email, code)
    except EmailDeliveryError:
        return False
    return True


def _dispatch_code_delivery(email: str, code: str) -> tuple[bool, bool]:
    if connection.in_atomic_block:
        transaction.on_commit(lambda: _deliver_code(email, code))
        logger.info("Verification email delivery deferred until transaction commit")
        return False, True
    return _deliver_code(email, code), False


def _consume_code(record, code: str, not_found_message: str) -> str | None:
    if record is None:
        return not_found_message
    if record.is_expired:
        return "Код истек. Запросите новый."
    if record.attempts_exhausted:
        return "Попытки исчерпаны. Запросите новый код."

    record.attempts += 1
    record.save(update_fields=["attempts"])

    if not record.matches(code):
        remaining = record.MAX_ATTEMPTS - record.attempts
        return f"Неверный код. Осталось попыток: {remaining}"

    record.delete()
    return None


def _purge_stale_registration(*, username: str, email: str) -> None:
    candidates = User.objects.filter(is_active=False).filter(
        Q(username=username) | Q(email__iexact=email)
    )
    for user in candidates:
        record = EmailVerificationCode.objects.filter(user=user).first()
        if record is not None and record.is_expired:
            user.delete()
            logger.info("Stale registration purged")


def purge_expired_registrations(*, batch_size: int = 1_000, dry_run: bool = False) -> PurgeResult:
    now = timezone.now()
    cutoff = now - EmailVerificationCode.TTL
    quota_cutoff = now - EmailDeliveryQuota.WINDOW
    with transaction.atomic():
        user_ids = list(
            User.objects.select_for_update()
            .filter(is_active=False, verification_code__created_at__lt=cutoff)
            .order_by("id")
            .values_list("id", flat=True)[:batch_size]
        )
        quota_ids = list(
            EmailDeliveryQuota.objects.select_for_update()
            .filter(window_started_at__lt=quota_cutoff)
            .order_by("id")
            .values_list("id", flat=True)[:batch_size]
        )
        if user_ids and not dry_run:
            User.objects.filter(pk__in=user_ids, is_active=False).delete()
        if quota_ids and not dry_run:
            EmailDeliveryQuota.objects.filter(pk__in=quota_ids).delete()

    if (user_ids or quota_ids) and not dry_run:
        logger.info(
            "Expired verification data purged",
            extra={"registrations": len(user_ids), "delivery_quotas": len(quota_ids)},
        )
    return PurgeResult(registrations=len(user_ids), delivery_quotas=len(quota_ids))


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
        validate_password(password, user=User(username=username, email=email))
    except DjangoValidationError as error:
        raise RegistrationError("; ".join(error.messages)) from None


def register_user(*, username: str, email: str, password: str) -> RegistrationResult:
    username = username.strip()
    email = email.strip().lower()

    with transaction.atomic():
        _purge_stale_registration(username=username, email=email)
        _validate_registration(username=username, email=email, password=password)

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password, is_active=False
            )
        except IntegrityError:
            raise RegistrationError("Имя пользователя или email уже используется") from None

        record = EmailVerificationCode(user=user)
        raw_code = _issue_code(record)
        record.save()
        _claim_email_delivery_quota(email)

    delivered, delivery_scheduled = _dispatch_code_delivery(email, raw_code)
    logger.info(
        "Registration created",
        extra={"delivered": delivered, "delivery_scheduled": delivery_scheduled},
    )
    return RegistrationResult(
        user=user,
        delivered=delivered,
        delivery_scheduled=delivery_scheduled,
        resend_available_in=record.cooldown_remaining,
    )


def resend_verification(*, user: User) -> RegistrationResult:
    # select_for_update сериализует параллельные resend'ы: cooldown и лимит
    # повторов нельзя обойти гонкой.
    with transaction.atomic():
        pending_user = (
            User.objects.select_for_update().filter(pk=user.pk, is_active=False).first()
        )
        if pending_user is None:
            raise VerificationError("Нет ожидающей подтверждения регистрации")
        record = (
            EmailVerificationCode.objects.select_for_update().filter(user=pending_user).first()
        )
        if record is None:
            raise VerificationError("Нет ожидающей подтверждения регистрации")
        now = timezone.now()
        if record.resend_window_expired(now):
            record.resend_count = 0
            record.resend_window_started_at = now

        code_matches_current_secret = (
            bool(record.code_nonce) and record.matches(record.current_code())
        )
        needs_new_code = (
            record.is_expired
            or record.attempts_exhausted
            or not code_matches_current_secret
        )
        if record.resends_exhausted:
            raise ResendLimitError(max(record.resend_window_remaining(now), 1))
        if not needs_new_code and record.cooldown_remaining > 0:
            raise ResendCooldownError(record.cooldown_remaining)

        if needs_new_code:
            raw_code = _issue_code(record)
        else:
            raw_code = record.current_code()
            record.last_sent_at = now
        record.resend_count += 1
        record.save(
            update_fields=[
                "code_hash", "code_nonce", "attempts", "created_at", "last_sent_at",
                "resend_count", "resend_window_started_at",
            ]
        )
        _claim_email_delivery_quota(pending_user.email)

    delivered, delivery_scheduled = _dispatch_code_delivery(pending_user.email, raw_code)
    return RegistrationResult(
        user=pending_user,
        delivered=delivered,
        delivery_scheduled=delivery_scheduled,
        resend_available_in=record.cooldown_remaining,
    )


def verify_email(*, user: User, code: str) -> User:
    with transaction.atomic():
        pending_user = (
            User.objects.select_for_update().filter(pk=user.pk, is_active=False).first()
        )
        record = (
            EmailVerificationCode.objects.select_for_update().filter(user=pending_user).first()
            if pending_user is not None
            else None
        )
        error = _consume_code(record, code, "Код не найден. Пройдите регистрацию заново.")
        if error is None:
            pending_user.is_active = True
            pending_user.save(update_fields=["is_active"])
    # Исключение бросаем после коммита: инкремент попытки должен сохраниться.
    if error is not None:
        raise VerificationError(error)
    return pending_user


def authenticate_user(*, request, username: str, password: str) -> User | None:
    return authenticate(request, username=username, password=password)


def update_nickname(*, user: User, nickname: str) -> None:
    cleaned = nickname.strip()
    if not cleaned or len(cleaned) > MAX_NICKNAME_LENGTH:
        raise ProfileError(f"Никнейм должен быть от 1 до {MAX_NICKNAME_LENGTH} символов")

    user.profile.nickname = cleaned
    user.profile.save(update_fields=["nickname"])
    logger.debug("Nickname changed")


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

    logger.debug("Avatar changed")
