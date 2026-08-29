import logging
import re

import bleach
from django.db.models import Count, Q

from . import moderation
from .models import Comment, CommentLike

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

URL_PATTERN = r'(https?://\S+|www\.\S+|\w+\.(com|ru|net|org|tk|xyz|bit|cc))'
MIN_LENGTH = 3
MAX_LENGTH = 900


class CommentRejected(Exception):
    pass


def create_comment(*, user, anime, text: str) -> Comment:
    cleaned = bleach.clean(text.strip(), tags=[], strip=True)
    # Спойлер-маркеры не участвуют в проверках содержимого
    plain = cleaned.replace("||", "")

    if re.search(URL_PATTERN, plain, re.IGNORECASE):
        security_logger.warning(f"Spam attempt blocked, user={user.username}, anime={anime.slug}")
        raise CommentRejected("Ссылки в комментариях запрещены")

    if not (MIN_LENGTH <= len(plain) <= MAX_LENGTH):
        raise CommentRejected("Недопустимая длина комментария")

    rejection = moderation.check_comment(plain)
    if rejection is not None:
        security_logger.warning(
            f"Comment rejected by moderation, user={user.username}, anime={anime.slug}, reason={rejection}"
        )
        raise CommentRejected(rejection)

    comment = Comment.objects.create(user=user, anime=anime, text=cleaned)
    logger.info(f"Comment {comment.id} created, anime={anime.slug}, user={user.username}, length={len(cleaned)}")
    return comment


def can_delete(*, user, comment: Comment) -> bool:
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or comment.user_id == user.id


def delete_comment(*, user, comment: Comment) -> None:
    comment_id, author = comment.id, comment.user.username
    comment.delete()
    logger.info(f"Comment {comment_id} deleted, by={user.username}, author={author}")


def comments_for_anime(anime):
    # annotate с агрегатами отбрасывает Meta.ordering, сортировка нужна явная
    return (
        anime.comments
        .select_related("user", "user__profile")
        .annotate(
            likes=Count("comment_likes", filter=Q(comment_likes__is_like=True)),
            dislikes=Count("comment_likes", filter=Q(comment_likes__is_like=False)),
        )
        .order_by("-created_at", "-id")
    )


def toggle_reaction(*, user, comment: Comment, is_like: bool) -> dict:
    like, created = CommentLike.objects.get_or_create(
        user=user,
        comment=comment,
        defaults={"is_like": is_like},
    )

    if not created:
        if like.is_like == is_like:
            like.delete()
        else:
            like.is_like = is_like
            like.save(update_fields=["is_like"])

    counts = comment.comment_likes.aggregate(
        likes=Count("id", filter=Q(is_like=True)),
        dislikes=Count("id", filter=Q(is_like=False)),
    )
    return {
        "likes": counts["likes"],
        "dislikes": counts["dislikes"],
        "rating": counts["likes"] - counts["dislikes"],
    }
