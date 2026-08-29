import os
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from catalog.models import AnimeDescription, ViewHistory
from comments.models import Comment


class SeedLoadtestCommandTest(TestCase):

    def test_seed_is_idempotent(self):
        call_command("seed_loadtest", "--force", "--users", "5", "--comments", "3", stdout=StringIO())
        first = User.objects.filter(username__startswith="loadtest_").count()
        call_command("seed_loadtest", "--force", "--users", "5", "--comments", "3", stdout=StringIO())
        second = User.objects.filter(username__startswith="loadtest_").count()
        self.assertEqual(first, 5)
        self.assertEqual(second, 5)

    def test_flush_removes_users_and_generated_views(self):
        call_command("seed_loadtest", "--force", "--users", "4", "--comments", "2", stdout=StringIO())
        user = User.objects.filter(username__startswith="loadtest_").first()
        anime = AnimeDescription.objects.first()
        ViewHistory.objects.create(anime=anime, user=user, ip_address="10.9.9.9")

        call_command("seed_loadtest", "--force", "--flush", stdout=StringIO())

        self.assertEqual(User.objects.filter(username__startswith="loadtest_").count(), 0)
        self.assertEqual(Comment.objects.count(), 0)
        self.assertFalse(ViewHistory.objects.exists())

    def test_reactions_only_on_loadtest_comments(self):
        anime = AnimeDescription.objects.first()
        real_user = User.objects.create_user(username="okabe", password="x")
        real_comment = Comment.objects.create(anime=anime, user=real_user, text="реальный комментарий")

        call_command("seed_loadtest", "--force", "--users", "5", "--comments", "3", stdout=StringIO())

        self.assertEqual(real_comment.comment_likes.count(), 0)

    def test_guard_requires_marker(self):
        with mock.patch.dict(os.environ, {"LOADTEST": ""}):
            with self.assertRaises(CommandError):
                call_command("seed_loadtest", "--users", "1", stdout=StringIO())


class ProfileQueriesCommandTest(TestCase):

    def test_runs_rolls_back_and_clears_cache(self):
        out = StringIO()
        call_command("profile_queries", "--force", stdout=out)

        self.assertFalse(AnimeDescription.objects.filter(slug__startswith="profile-").exists())
        self.assertIsNone(cache.get("catalog:anime_list"))
        self.assertIn("N+1", out.getvalue())
