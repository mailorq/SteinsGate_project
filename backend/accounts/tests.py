import io
import shutil
import tempfile
from datetime import timedelta
from smtplib import SMTPException
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from PIL import Image

from . import lockout, services
from .models import EmailVerificationCode

User = get_user_model()


def csrf_headers(client):
    client.get("/api/auth/csrf")
    return {"HTTP_X_CSRFTOKEN": client.cookies["csrftoken"].value}


class RegistrationServiceTest(TestCase):

    def test_email_domain_validation(self):
        with self.assertRaises(services.RegistrationError):
            services.register_user(
                username='test', email='test@blocked.com', password='complex_pass_123'
            )

    def test_duplicate_email_rejected(self):
        User.objects.create_user(username='taken', email='taken@gmail.com', password='x')

        with self.assertRaises(services.RegistrationError):
            services.register_user(
                username='newuser', email='taken@gmail.com', password='complex_pass_123'
            )

    def test_duplicate_username_rejected(self):
        User.objects.create_user(username='taken', email='one@gmail.com', password='x')

        with self.assertRaises(services.RegistrationError):
            services.register_user(
                username='taken', email='two@gmail.com', password='complex_pass_123'
            )

    def test_weak_password_rejected(self):
        with self.assertRaises(services.RegistrationError):
            services.register_user(
                username='test', email='test@gmail.com', password='12345678'
            )


class VerificationServiceTest(TestCase):

    def setUp(self):
        self.user = services.register_user(
            username='kurisu',
            email='kurisu@gmail.com',
            password='complex_pass_123',
        )

    def test_registered_user_is_inactive_with_code(self):
        self.assertFalse(self.user.is_active)
        self.assertEqual(len(self.user.verification_code.code), 6)

    def test_correct_code_activates_user(self):
        services.verify_email(user=self.user, code=self.user.verification_code.code)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertFalse(EmailVerificationCode.objects.filter(user=self.user).exists())

    def test_wrong_code_raises_and_keeps_user_inactive(self):
        with self.assertRaises(services.VerificationError):
            services.verify_email(user=self.user, code='000000')

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_attempts_are_limited(self):
        for _ in range(EmailVerificationCode.MAX_ATTEMPTS):
            with self.assertRaises(services.VerificationError):
                services.verify_email(user=self.user, code='000000')

        with self.assertRaises(services.VerificationError):
            services.verify_email(user=self.user, code=self.user.verification_code.code)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_expired_code_rejected(self):
        record = self.user.verification_code
        record.created_at = timezone.now() - EmailVerificationCode.TTL - timedelta(minutes=1)
        record.save(update_fields=['created_at'])

        with self.assertRaises(services.VerificationError):
            services.verify_email(user=self.user, code=record.code)

    def test_inactive_user_cannot_login(self):
        logged_in = self.client.login(username='kurisu', password='complex_pass_123')

        self.assertFalse(logged_in)


class LockoutTest(TestCase):

    def setUp(self):
        cache.clear()
        User.objects.create_user(username='okabe', password='correct_horse_1')

    def login(self, password):
        return self.client.post(
            '/api/auth/login',
            {'username': 'okabe', 'password': password},
            content_type='application/json',
        )

    def test_soft_block_after_five_failures(self):
        for _ in range(5):
            self.assertEqual(self.login('wrong').status_code, 400)

        blocked = self.login('wrong')
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('Повторите через', blocked.json()['detail'])

        also_blocked_with_correct = self.login('correct_horse_1')
        self.assertEqual(also_blocked_with_correct.status_code, 429)

    def test_success_resets_counter(self):
        for _ in range(4):
            self.login('wrong')

        self.assertEqual(self.login('correct_horse_1').status_code, 200)

        for _ in range(5):
            self.assertEqual(self.login('wrong').status_code, 400)

    def test_hard_block_after_twenty_failures(self):
        for _ in range(lockout.HARD_LIMIT):
            lockout.register_failure('login', '1.2.3.4')

        with self.assertRaises(lockout.LockedOut) as caught:
            lockout.check_blocked('login', '1.2.3.4')

        self.assertGreater(caught.exception.retry_after, lockout.SOFT_BLOCK_SECONDS)

    def test_five_fresh_attempts_after_block_expires(self):
        for _ in range(5):
            lockout.register_failure('login', '5.6.7.8')

        with self.assertRaises(lockout.LockedOut):
            lockout.check_blocked('login', '5.6.7.8')

        cache.delete('lockout:login:5.6.7.8:block')

        for _ in range(4):
            lockout.register_failure('login', '5.6.7.8')
        lockout.check_blocked('login', '5.6.7.8')

        lockout.register_failure('login', '5.6.7.8')
        with self.assertRaises(lockout.LockedOut):
            lockout.check_blocked('login', '5.6.7.8')

    def test_verify_email_lockout(self):
        response = self.client.post(
            '/api/auth/register',
            {'username': 'kurisu', 'email': 'kurisu@gmail.com', 'password': 'complex_pass_123'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)

        for _ in range(5):
            wrong = self.client.post(
                '/api/auth/verify-email', {'code': '000000'}, content_type='application/json'
            )
            self.assertEqual(wrong.status_code, 400)

        blocked = self.client.post(
            '/api/auth/verify-email', {'code': '000000'}, content_type='application/json'
        )
        self.assertEqual(blocked.status_code, 429)


class AuthApiTest(TestCase):

    def setUp(self):
        cache.clear()

    REGISTER_PAYLOAD = {
        'username': 'kurisu',
        'email': 'kurisu@gmail.com',
        'password': 'complex_pass_123',
    }

    def register(self):
        return self.client.post(
            '/api/auth/register', self.REGISTER_PAYLOAD, content_type='application/json'
        )

    def test_register_creates_inactive_user_and_sends_email(self):
        response = self.register()

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='kurisu')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verification', mail.outbox[0].subject.lower())

    def test_register_rejects_bad_domain(self):
        response = self.client.post(
            '/api/auth/register',
            {**self.REGISTER_PAYLOAD, 'email': 'kurisu@blocked.com'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='kurisu').exists())

    def test_full_registration_flow(self):
        self.register()
        user = User.objects.get(username='kurisu')

        wrong = self.client.post(
            '/api/auth/verify-email', {'code': '000000'}, content_type='application/json'
        )
        self.assertEqual(wrong.status_code, 400)

        response = self.client.post(
            '/api/auth/verify-email',
            {'code': user.verification_code.code},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'kurisu')
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertEqual(user.profile.nickname, 'kurisu')

    def test_verify_without_pending_registration(self):
        response = self.client.post(
            '/api/auth/verify-email', {'code': '123456'}, content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_login_and_session(self):
        User.objects.create_user(username='daru', password='super_haker_123')

        anonymous = self.client.get('/api/auth/session')
        self.assertIsNone(anonymous.json()['user'])

        bad = self.client.post(
            '/api/auth/login',
            {'username': 'daru', 'password': 'wrong'},
            content_type='application/json',
        )
        self.assertEqual(bad.status_code, 400)

        response = self.client.post(
            '/api/auth/login',
            {'username': 'daru', 'password': 'super_haker_123'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], 'daru')

        session = self.client.get('/api/auth/session')
        self.assertEqual(session.json()['user']['username'], 'daru')

    def test_logout(self):
        User.objects.create_user(username='daru', password='super_haker_123')
        self.client.login(username='daru', password='super_haker_123')

        response = self.client.post('/api/auth/logout', **csrf_headers(self.client))

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(self.client.get('/api/auth/session').json()['user'])


class ProfileApiTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='okabe', password='elpsykongroo')
        self.client.login(username='okabe', password='elpsykongroo')

    def test_update_nickname(self):
        response = self.client.patch(
            '/api/profile',
            {'nickname': 'Hououin Kyouma'},
            content_type='application/json',
            **csrf_headers(self.client),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['nickname'], 'Hououin Kyouma')
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.nickname, 'Hououin Kyouma')

    def test_anonymous_cannot_update_profile(self):
        self.client.logout()

        response = self.client.patch(
            '/api/profile', {'nickname': 'x'}, content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)


class CsrfEnforcementTest(TestCase):
    """django-ninja снимает CSRF со всех view, маршруты без auth проверяют сами"""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.payload = {
            'username': 'okabe',
            'email': 'okabe@gmail.com',
            'password': 'complex_pass_123',
        }

    def test_register_without_token_rejected(self):
        response = self.client.post(
            '/api/auth/register', self.payload, content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='okabe').exists())

    def test_login_without_token_rejected(self):
        response = self.client.post(
            '/api/auth/login',
            {'username': 'okabe', 'password': 'complex_pass_123'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_verify_without_token_rejected(self):
        response = self.client.post(
            '/api/auth/verify-email', {'code': '123456'}, content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)

    def test_register_with_token_accepted(self):
        response = self.client.post(
            '/api/auth/register',
            self.payload,
            content_type='application/json',
            **csrf_headers(self.client),
        )
        self.assertEqual(response.status_code, 201)


class EmailDeliveryFailureTest(TestCase):
    """Недоступный SMTP должен давать 503, а не 500, и не оставлять аккаунт"""

    def test_smtp_failure_returns_503_and_rolls_back(self):
        client = Client()
        payload = {
            'username': 'daru',
            'email': 'daru@gmail.com',
            'password': 'complex_pass_123',
        }

        with patch(
            'accounts.services.send_mail', side_effect=SMTPException('smtp is down')
        ):
            response = client.post(
                '/api/auth/register',
                payload,
                content_type='application/json',
                **csrf_headers(client),
            )

        self.assertEqual(response.status_code, 503)
        self.assertFalse(User.objects.filter(username='daru').exists())

    def test_connection_refused_is_handled(self):
        with patch('accounts.services.send_mail', side_effect=ConnectionRefusedError()):
            with self.assertRaises(services.EmailDeliveryError):
                services.register_user(
                    username='daru', email='daru@gmail.com', password='complex_pass_123'
                )

        self.assertFalse(User.objects.filter(username='daru').exists())


class StaleRegistrationTest(TestCase):

    def test_expired_unverified_registration_frees_email(self):
        first = services.register_user(
            username='squatter', email='victim@gmail.com', password='complex_pass_123'
        )
        record = EmailVerificationCode.objects.get(user=first)
        record.created_at = timezone.now() - EmailVerificationCode.TTL - timedelta(minutes=1)
        record.save(update_fields=['created_at'])

        second = services.register_user(
            username='victim', email='victim@gmail.com', password='complex_pass_123'
        )

        self.assertNotEqual(first.pk, second.pk)
        self.assertFalse(User.objects.filter(pk=first.pk).exists())

    def test_disabled_account_is_not_purged(self):
        banned = User.objects.create_user(
            username='banned', email='banned@gmail.com', password='x', is_active=False
        )

        with self.assertRaises(services.RegistrationError):
            services.register_user(
                username='banned', email='banned@gmail.com', password='complex_pass_123'
            )

        self.assertTrue(User.objects.filter(pk=banned.pk).exists())

    def test_pending_registration_still_blocks(self):
        services.register_user(
            username='squatter', email='victim@gmail.com', password='complex_pass_123'
        )

        with self.assertRaises(services.RegistrationError):
            services.register_user(
                username='victim', email='victim@gmail.com', password='complex_pass_123'
            )


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='sg-avatar-test-'))
class AvatarValidationTest(TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._overridden_settings['MEDIA_ROOT'], ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username='mayuri', email='mayuri@gmail.com', password='complex_pass_123'
        )

    @staticmethod
    def _png(color: str = 'red') -> SimpleUploadedFile:
        buffer = io.BytesIO()
        Image.new('RGB', (8, 8), color).save(buffer, format='PNG')
        return SimpleUploadedFile('avatar.png', buffer.getvalue(), content_type='image/png')

    def test_disguised_file_rejected(self):
        payload = SimpleUploadedFile(
            'avatar.png', b'<html><script>alert(1)</script></html>', content_type='image/png'
        )

        with self.assertRaises(services.ProfileError):
            services.update_avatar(user=self.user, avatar=payload)

        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.avatar)

    def test_real_image_accepted(self):
        services.update_avatar(user=self.user, avatar=self._png())

        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.avatar)

    def test_previous_file_removed_on_replace(self):
        services.update_avatar(user=self.user, avatar=self._png('red'))
        profile = self.user.profile
        profile.refresh_from_db()
        first_path = profile.avatar.path
        storage = profile.avatar.storage

        services.update_avatar(user=self.user, avatar=self._png('blue'))
        profile.refresh_from_db()

        self.assertNotEqual(profile.avatar.path, first_path)
        self.assertFalse(storage.exists(first_path))
