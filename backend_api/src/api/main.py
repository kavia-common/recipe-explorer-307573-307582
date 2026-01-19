from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as api_router
from src.api.storage import Store

openapi_tags = [
    {"name": "categories", "description": "Browse recipe categories."},
    {"name": "recipes", "description": "Browse/search recipes and fetch recipe details."},
    {"name": "favorites", "description": "Save and list user favorites."},
    {"name": "ratings", "description": "Create/read user ratings for recipes."},
]

app = FastAPI(
    title="Recipe Explorer API",
    description=(
        "Recipe Explorer backend API providing recipe browsing, ingredient search, "
        "favorites, and user ratings."
    ),
    version="0.2.0",
    openapi_tags=openapi_tags,
)

# Allow the React frontend (default dev server port 3000) and local development.
# In hosted environments, requests come from a different origin; allow all as fallback.
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup_load_store() -> None:
    # Keep persistence minimal: a JSON file in backend_api/data/store.json.
    app.state.store = Store.load()


@app.get("/", tags=["health"], summary="Health check", operation_id="health_check")
# PUBLIC_INTERFACE
def health_check():
    """Health check endpoint used by infra/CI to verify the service is running."""
    return {"message": "Healthy"}


app.include_router(api_router)
