from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from app.api.routes.profile import router as profile_router
from app.api.routes.auth import router as auth_router
from app.api.routes.trips import router as trips_router
from app.api.routes.reservations import router as reservations_router
from app.api.routes.messages import router as messages_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.admin import router as admin_router

# Rate limiter en mémoire, basé sur l'adresse IP de la requête.
# Suffisant pour un seul serveur ; si l'app est un jour déployée sur
# plusieurs instances, migrer vers un backend Redis partagé
# (limiter = Limiter(key_func=get_remote_address, storage_uri="redis://...")).
limiter = Limiter(key_func=get_remote_address)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Ajoute des en-têtes HTTP de sécurité standards à chaque réponse."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # HSTS : force HTTPS côté navigateur une fois en prod avec un vrai certificat.
        # Inoffensif en dev sur http://127.0.0.1 (le navigateur l'ignore hors HTTPS).
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

MAX_REQUEST_SIZE_BYTES = 10 * 1024 * 1024  # 10 Mo (couvre les uploads d'images/documents)


class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    """Rejette les requêtes dont le corps dépasse une taille raisonnable,
    avant même qu'elles ne soient traitées par les routes."""

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE_BYTES:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=413,
                content={"detail": "Le corps de la requête est trop volumineux."},
            )
        return await call_next(request)

app = FastAPI(title="TripMatch API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LimitRequestSizeMiddleware)

# CORS — nécessaire pour que l'app Flutter (web, en dev) puisse appeler l'API.
# En développement, on autorise toutes les origines pour simplifier.
# À restreindre à des domaines précis avant la mise en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # ← changé de True à False
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(trips_router)
app.include_router(reservations_router)
app.include_router(messages_router)
app.include_router(notifications_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "TripMatch API is running"}