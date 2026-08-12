from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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

app = FastAPI(title="TripMatch API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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