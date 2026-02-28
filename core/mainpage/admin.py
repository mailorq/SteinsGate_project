from django.contrib import admin
from .models import AnimeDescription, Comment, CommentLike, AnimeRating, ViewHistory, WatchProgress

admin.site.register(AnimeDescription)
admin.site.register(Comment)
admin.site.register(CommentLike)
admin.site.register(AnimeRating)
admin.site.register(ViewHistory)
admin.site.register(WatchProgress)