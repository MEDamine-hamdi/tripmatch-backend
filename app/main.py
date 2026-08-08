from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.profile import router as profile_router
from app.api.routes.auth import router as auth_router
from app.api.routes.trips import router as trips_router
from app.api.routes.reservations import router as reservations_router
from app.api.routes.messages import router as messages_router


app = FastAPI(title="TripMatch API", version="0.1.0")

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
@app.get("/")
def root():
    return {"message": "TripMatch API is running"}