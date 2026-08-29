from datetime import datetime

from ninja import Schema
from pydantic import Field


class CommentAuthorOut(Schema):
    username: str
    nickname: str
    avatar_url: str | None


class CommentOut(Schema):
    id: int
    author: CommentAuthorOut
    text: str
    created_at: datetime
    likes: int
    dislikes: int
    my_reaction: str | None
    can_delete: bool


class CommentPageOut(Schema):
    items: list[CommentOut]
    page: int
    total_pages: int
    total: int


class CommentIn(Schema):
    text: str = Field(min_length=3, max_length=900)


class ReactionIn(Schema):
    is_like: bool


class ReactionOut(Schema):
    likes: int
    dislikes: int
    rating: int
