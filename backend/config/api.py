from django.conf import settings
from ninja import NinjaAPI

from accounts.api import auth_router, profile_router
from catalog.api import router as catalog_router
from comments.api import router as comments_router
from watch.api import router as watch_router

api = NinjaAPI(
    title="SteinsGate API",
    version="1.0.0",
    # docs_url прячет только Swagger UI, сама схема живет на openapi_url
    docs_url="/docs" if settings.API_DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.API_DOCS_ENABLED else None,
)

api.add_router("/auth", auth_router)
api.add_router("/profile", profile_router)
api.add_router("", catalog_router)
api.add_router("", comments_router)
api.add_router("", watch_router)
