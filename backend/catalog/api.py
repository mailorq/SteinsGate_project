from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth

from accounts.schemas import MessageOut
from config.network import get_client_ip
from config.throttling import auth_throttles

from . import services
from .models import AnimeDescription
from .schemas import AnimeDetailOut, AnimeListOut, RatingIn, RatingOut

router = Router(tags=["catalog"])

WRITE_THROTTLES = auth_throttles(settings.API_WRITE_THROTTLE, settings.API_WRITE_THROTTLE_SUSTAINED)


@router.get("/anime", response=list[AnimeListOut])
def list_anime(request):
    return services.anime_list()


@router.get("/anime/{slug}", response=AnimeDetailOut)
def anime_detail(request, slug: str):
    anime = get_object_or_404(AnimeDescription, slug=slug)

    services.register_view_event(
        anime=anime,
        user=request.user,
        ip_address=get_client_ip(request),
    )

    user_rating = None
    if request.user.is_authenticated:
        rating = request.user.anime_ratings.filter(anime=anime).first()
        user_rating = rating.rating if rating else None

    return {
        "slug": anime.slug,
        "name": anime.name,
        "season": anime.appearing,
        "type": anime.type,
        "genres": anime.genres,
        "description": anime.description,
        "avg_rating": services.average_rating(anime),
        "total_views": services.total_views(anime),
        "user_rating": user_rating,
    }


@router.post(
    "/anime/{slug}/rating",
    response={200: RatingOut, 400: MessageOut},
    auth=django_auth,
    throttle=WRITE_THROTTLES,
)
def rate_anime(request, slug: str, payload: RatingIn):
    anime = get_object_or_404(AnimeDescription, slug=slug)

    try:
        avg_rating = services.rate_anime(user=request.user, anime=anime, rating=payload.rating)
    except ValueError as error:
        return 400, {"detail": str(error)}

    return 200, {
        "avg_rating": round(avg_rating, 1) if avg_rating else 0,
        "user_rating": payload.rating,
    }
