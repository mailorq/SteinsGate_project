from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class AnimeDescription(models.Model):
    name = models.CharField(max_length=255, unique=True)
    appearing = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    genres = models.CharField(max_length=500)
    description = models.TextField()
    poster = models.ImageField(upload_to="posters/", blank=True, default="")
    URL_MAP = {
        "Steins;Gate": "steins_gate_page",
        "Steins;Gate 0": "steins_gate_zero_page",
        "Steins;Gate: Load Region of Deja Vu": "steins_gate_load_region",
        "Steins;Gate: Kyoukaimenjou no Missing Link": "steins_gate_missing_link",
    }

    def get_absolute_url(self):
        url_name = self.URL_MAP.get(self.name)
        if url_name:
            return reverse(url_name)
        return "/"

    def __str__(self):
        return self.name


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="anime_comments")
    anime = models.ForeignKey(AnimeDescription, on_delete=models.CASCADE, related_name="comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.anime.name}"

    @property
    def likes_count(self):
        return self.comment_likes.filter(is_like=True).count()

    @property
    def dislikes_count(self):
        return self.comment_likes.filter(is_like=False).count()

    @property
    def rating(self):
        return self.likes_count - self.dislikes_count


class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_likes")
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="comment_likes")
    is_like = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username} - {'Like' if self.is_like else 'Dislike'} - {self.comment.id}"


class AnimeRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="anime_ratings")
    anime = models.ForeignKey(AnimeDescription, on_delete=models.CASCADE, related_name="ratings")
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'anime')

    def __str__(self):
        return f"{self.user.username} - {self.anime.name} - {self.rating}"


class ViewHistory(models.Model):
    anime = models.ForeignKey(AnimeDescription, on_delete=models.CASCADE, related_name="views")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="view_history")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.anime.name} - {self.viewed_at}"


class WatchProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watch_progress")
    anime = models.ForeignKey(AnimeDescription, on_delete=models.CASCADE, related_name="watch_progress")
    current_time = models.FloatField(default=0)
    duration = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'anime')
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.anime.name} - {self.current_time}s"

    @property
    def progress_percentage(self):
        if self.duration > 0:
            return (self.current_time / self.duration) * 100
        return 0
