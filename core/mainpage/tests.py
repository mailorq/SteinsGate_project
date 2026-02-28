from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import AnimeDescription, Comment

User = get_user_model()


class AnimeModelTest(TestCase):

    def setUp(self):
        self.anime = AnimeDescription.objects.create(
            name="Steins;Gate",
            description="Аниме про путешествия во времени"
        )

    def test_anime_str_representation(self):
        self.assertEqual(str(self.anime), "Steins;Gate")

    def test_anime_has_no_comments_initially(self):
        self.assertEqual(self.anime.comments.count(), 0)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='okabe',
            email='okabe@lab.mem',
            password='elpsykongroo'
        )
        self.anime = AnimeDescription.objects.create(
            name="Steins;Gate 0"
        )

    def test_comment_creation(self):
        comment = Comment.objects.create(
            user=self.user,
            anime=self.anime,
            text="Лучшее аниме!"
        )

        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.anime, self.anime)
        self.assertIn("Лучшее", comment.text)

    def test_comment_belongs_to_anime(self):
        Comment.objects.create(
            user=self.user,
            anime=self.anime,
            text="test"
        )

        self.assertEqual(self.anime.comments.count(), 1)
        self.assertEqual(self.anime.comments.first().user, self.user)


class SteinsGatePageTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('steins_gate_page')

    def test_page_loads_successfully(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'steins-gate_page.html')

    def test_page_contains_anime_title(self):
        response = self.client.get(self.url)

        self.assertContains(response, 'Steins;Gate')

    def test_divergence_meter_present(self):
        response = self.client.get(self.url)

        self.assertContains(response, 'nixie-digit')
        self.assertContains(response, '0.337187')


class CommentFunctionalityTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mayuri',
            password='tuturu'
        )
        self.anime = AnimeDescription.objects.create(name="Steins;Gate")
        self.url = reverse('steins_gate_page')

    def test_anonymous_user_cannot_comment(self):
        response = self.client.post(self.url, {
            'comment': 'Тест коммент'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 0)

    def test_logged_in_user_can_comment(self):
        self.client.login(username='mayuri', password='tuturu')

        response = self.client.post(self.url, {
            'comment': 'Tuturu~!'
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.count(), 1)

        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Tuturu~!')
        self.assertEqual(comment.user, self.user)

    def test_empty_comment_not_saved(self):
        self.client.login(username='mayuri', password='tuturu')

        self.client.post(self.url, {'comment': '   '})

        self.assertEqual(Comment.objects.count(), 0)


class PaginationTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='pass')
        self.anime = AnimeDescription.objects.create(name="Steins;Gate")

        for i in range(10):
            Comment.objects.create(
                user=self.user,
                anime=self.anime,
                text=f"Коммент {i}"
            )

        self.url = reverse('steins_gate_page')

    def test_first_page_has_6_comments(self):
        response = self.client.get(self.url)

        self.assertEqual(len(response.context['comments']), 6)

    def test_second_page_has_remaining_comments(self):
        response = self.client.get(f'{self.url}?page=2')

        self.assertEqual(len(response.context['comments']), 4)


class URLTest(TestCase):

    def test_steins_gate_url_resolves(self):
        url = reverse('steins_gate_page')
        self.assertEqual(url, '/steins-gate/')

    def test_steins_gate_zero_url_resolves(self):
        url = reverse('steins_gate_zero_page')
        self.assertEqual(url, '/steins-gate-zero/')

    def test_future_gadget_lab_url_resolves(self):
        url = reverse('future_gadget_laboratory')
        self.assertEqual(url, '/future-gadget-laboratory/')


class AuthenticationTest(TestCase):

    def test_user_can_register_with_email_verification(self):

        response = self.client.post(reverse('register'), {
            'username': 'kurisu',
            'email': 'kurisu@gmail.com',
            'password': 'complex_pass_123',
            'confirm_password': 'complex_pass_123'
        })

        self.assertRedirects(response, reverse('email_verification'))

        self.assertFalse(User.objects.filter(username='kurisu').exists())

        self.assertIn('verification_code', self.client.session)
        self.assertIn('registration_data', self.client.session)

        code = self.client.session['verification_code']
        response = self.client.post(reverse('email_verification'), {'code': str(code)})

        self.assertTrue(User.objects.filter(username='kurisu').exists())

        user = User.objects.get(username='kurisu')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

        self.assertTrue(hasattr(user, 'profile'))
        self.assertEqual(user.profile.nickname, 'kurisu')

    def test_register_sends_email(self):
        from django.core import mail

        self.client.post(reverse('register'), {
            'username': 'daru',
            'email': 'daru@gmail.com',
            'password': 'super_haker_123',
            'confirm_password': 'super_haker_123'
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verification', mail.outbox[0].subject.lower())
        self.assertEqual(mail.outbox[0].to, ['daru@gmail.com'])

    def test_wrong_verification_code_fails(self):

        self.client.post(reverse('register'), {
            'username': 'mayuri',
            'email': 'mayuri@gmail.com',
            'password': 'tuturu_123',
            'confirm_password': 'tuturu_123'
        })

        self.client.post(reverse('email_verification'), {
            'code': '000000'
        })

        self.assertFalse(User.objects.filter(username='mayuri').exists())

    def test_email_domain_validation(self):

        response = self.client.post(reverse('register'), {
            'username': 'test',
            'email': 'test@blocked.com',
            'password': 'pass_123',
            'confirm_password': 'pass_123'
        })

        form = response.context['form']
        self.assertIn('email', form.errors)

    def test_user_can_login(self):
        User.objects.create_user(username='daru', password='super_haker')

        logged_in = self.client.login(username='daru', password='super_haker')

        self.assertTrue(logged_in)