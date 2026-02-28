from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from .models import AnimeDescription, Comment, CommentLike, AnimeRating, ViewHistory, WatchProgress
from .constants import ANIME_DEFAULTS, ANIME_POSTERS, ANIME_PLAYERS, ANIME_QUESTIONS
import logging
import bleach
import re

logger = logging.getLogger(__name__)

def _anime_page(request, anime_name, template):

    anime, _ = AnimeDescription.objects.get_or_create(name=anime_name,defaults=ANIME_DEFAULTS[anime_name],)
    
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    ViewHistory.objects.create(
        anime=anime,
        user=request.user if request.user.is_authenticated else None,
        ip_address=get_client_ip(request)
    )

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(request.path)

        comment_text = request.POST.get("comment", "").strip()

        comment_text = bleach.clean(comment_text, tags=[], strip=True)

        url_pattern = r'(https?://\S+|www\.\S+|\w+\.(com|ru|net|org|tk|xyz|bit|cc))'

        if re.search(url_pattern, comment_text, re.IGNORECASE):
            logger.warning(f"Spam attempt blocked: {request.user.username} tried to post a link.")
            return redirect(request.path)

        if comment_text and 2 < len(comment_text) < 2000:
            Comment.objects.create(user=request.user, anime=anime, text=comment_text)
            logger.info(f"Anime {anime_name} comment {comment_text} , user={request.user.username}" )

        return redirect(request.path)

    comments = anime.comments.select_related("user", "user__profile").prefetch_related("comment_likes")
    paginator = Paginator(comments, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    user_rating = None
    watch_progress = None
    if request.user.is_authenticated:
        user_rating = AnimeRating.objects.filter(user=request.user, anime=anime).first()
        watch_progress = WatchProgress.objects.filter(user=request.user, anime=anime).first()
    
    avg_rating = anime.ratings.aggregate(Avg('rating'))['rating__avg']
    total_views = anime.views.count()

    poster = ANIME_POSTERS.get(anime_name, "")
    players = ANIME_PLAYERS.get(anime_name, {})

    return render(request, template, {
        "anime": anime,
        "comments": page_obj,
        "poster": poster,
        "players": players,
        "questions": ANIME_QUESTIONS,
        "user_rating": user_rating,
        "avg_rating": avg_rating,
        "total_views": total_views,
        "watch_progress": watch_progress,
    })

def steins_gate_page(request):
    logger.info(f"Steins Gate page opened , user={request.user.username if request.user.is_authenticated else None}")
    return _anime_page(request, "Steins;Gate", "steins-gate_page.html")

def steins_gate_zero_page(request):
    logger.info(f"Steins Gate zero page opened , user={request.user.username if request.user.is_authenticated else None}")
    return _anime_page(request, "Steins;Gate 0", "steins-gate-zero_page.html")

def steins_gate_load_region_page(request):
    logger.info(f"Steins Gate: Load Region of Deja Vu page opened, user={request.user.username if request.user.is_authenticated else None}")
    return _anime_page(request, "Steins;Gate: Load Region of Deja Vu", "steins_gate_load_region_page.html")

def steins_gate_missing_link(request):
    logger.info(f"Steins Gate: Kyoukaimenjou no Missing Link, user={request.user.username if request.user.is_authenticated else None}")
    return _anime_page(request, "Steins;Gate: Kyoukaimenjou no Missing Link", "steins_gate_missing_link.html")

def future_gadget_laboratory_page(request):
    logger.info(f"Future Gadget Laboratory page opened , user={request.user.username if request.user.is_authenticated else None}")
    
    popular_anime = AnimeDescription.objects.annotate(
        views_count=Count('views')
    ).order_by('-views_count')[:4]
    
    return render(request, "future_gadget_laboratory.html", {"popular_anime": popular_anime})

@login_required
def toggle_comment_like(request, comment_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    comment = get_object_or_404(Comment, id=comment_id)
    is_like = request.POST.get("is_like") == "true"
    
    like, created = CommentLike.objects.get_or_create(
        user=request.user,
        comment=comment,
        defaults={"is_like": is_like}
    )
    
    if not created:
        if like.is_like == is_like:
            like.delete()
        else:
            like.is_like = is_like
            like.save()
    
    return JsonResponse({
        "likes": comment.likes_count,
        "dislikes": comment.dislikes_count,
        "rating": comment.rating
    })

@login_required
def rate_anime(request, anime_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    anime = get_object_or_404(AnimeDescription, id=anime_id)
    rating_value = int(request.POST.get("rating", 0))
    
    if not (1 <= rating_value <= 5):
        return JsonResponse({"error": "Invalid rating"}, status=400)
    
    rating, created = AnimeRating.objects.update_or_create(
        user=request.user,
        anime=anime,
        defaults={"rating": rating_value}
    )
    
    avg_rating = anime.ratings.aggregate(Avg('rating'))['rating__avg']
    
    return JsonResponse({
        "success": True,
        "avg_rating": round(avg_rating, 1) if avg_rating else 0,
        "user_rating": rating_value
    })

@login_required
def save_watch_progress(request, anime_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    anime = get_object_or_404(AnimeDescription, id=anime_id)
    current_time = float(request.POST.get("current_time", 0))
    duration = float(request.POST.get("duration", 0))
    
    progress, created = WatchProgress.objects.update_or_create(
        user=request.user,
        anime=anime,
        defaults={
            "current_time": current_time,
            "duration": duration
        }
    )
    
    return JsonResponse({
        "success": True,
        "current_time": progress.current_time,
        "duration": progress.duration,
        "percentage": progress.progress_percentage
    })

def sitemap_view(request):
    return render(request, "sitemap.xml", content_type="application/xml")

def robots_view(request):
    return render(request, "robots.txt", content_type="text/plain")