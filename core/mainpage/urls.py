from django.urls import path
from django.views.generic import RedirectView
from .views import (
    steins_gate_page, steins_gate_zero_page, steins_gate_load_region_page, 
    steins_gate_missing_link, future_gadget_laboratory_page,
    toggle_comment_like, rate_anime, sitemap_view, robots_view, save_watch_progress
)

urlpatterns = [
    path("future-gadget-laboratory/", future_gadget_laboratory_page, name="future_gadget_laboratory"),
    path("", RedirectView.as_view(pattern_name='steins_gate_page')),
    path("steins-gate/", steins_gate_page, name="steins_gate_page"),
    path("steins-gate-zero/", steins_gate_zero_page, name="steins_gate_zero_page"),
    path("steins-gate-load-region-of-deja-vu/", steins_gate_load_region_page, name="steins_gate_load_region"),
    path("steins-gate-kyoukaimenjou-no-missing-link/", steins_gate_missing_link, name="steins_gate_missing_link"),
    path("comment/<int:comment_id>/like/", toggle_comment_like, name="toggle_comment_like"),
    path("anime/<int:anime_id>/rate/", rate_anime, name="rate_anime"),
    path("anime/<int:anime_id>/progress/", save_watch_progress, name="save_watch_progress"),
    path("sitemap.xml", sitemap_view, name="sitemap"),
    path("robots.txt", robots_view, name="robots"),
]
