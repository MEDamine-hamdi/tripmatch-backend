from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router

app = FastAPI(title="TripMatch API", version="0.1.0")

# CORS — nécessaire pour que l'app Flutter (web, en dev) puisse appeler l'API.
# En développement, on autorise toutes les origines pour simplifier.
# À restreindre à des domaines précis avant la mise en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "TripMatch API is running"}