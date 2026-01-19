from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Query

from src.api.models import (
    Category,
    FavoriteCreate,
    Message,
    Rating,
    RatingCreate,
    Recipe,
    SearchResponse,
)
from src.api.storage import Store

router = APIRouter()


def _get_store(request) -> Store:
    # Store is attached to app.state in main.py; this is a small helper.
    return request.app.state.store


@router.get(
    "/categories",
    response_model=List[Category],
    tags=["categories"],
    summary="List categories",
    description="Returns all recipe categories.",
    operation_id="list_categories",
)
# PUBLIC_INTERFACE
def list_categories(request) -> List[Category]:
    """List all categories."""
    store = _get_store(request)
    return sorted(store.categories.values(), key=lambda c: c.name.lower())


@router.get(
    "/recipes",
    response_model=SearchResponse,
    tags=["recipes"],
    summary="List/search recipes",
    description=(
        "List recipes with optional filters:\n"
        "- category_id\n"
        "- q (search in title/description)\n"
        "- ingredients (comma-separated list; all must match)"
    ),
    operation_id="list_recipes",
)
# PUBLIC_INTERFACE
def list_recipes(
    request,
    category_id: Optional[str] = Query(default=None, description="Filter by category id."),
    q: Optional[str] = Query(default=None, description="Text search query."),
    ingredients: Optional[str] = Query(
        default=None, description="Comma-separated ingredient terms (AND match)."
    ),
) -> SearchResponse:
    """List or search recipes."""
    store = _get_store(request)
    ingredients_list: Optional[List[str]] = None
    if ingredients is not None:
        ingredients_list = [p.strip() for p in ingredients.split(",")]
    recipes = store.list_recipes(category_id=category_id, q=q, ingredients=ingredients_list)
    items = [store.recipe_to_summary(r) for r in recipes]
    return SearchResponse(items=items, total=len(items))


@router.get(
    "/recipes/{recipe_id}",
    response_model=Recipe,
    tags=["recipes"],
    summary="Get recipe detail",
    description="Returns a full recipe including ingredients and instructions.",
    operation_id="get_recipe",
)
# PUBLIC_INTERFACE
def get_recipe(request, recipe_id: str) -> Recipe:
    """Get one recipe by id."""
    store = _get_store(request)
    recipe = store.get_recipe_or_404(recipe_id)
    return store.recipe_to_full(recipe)


@router.get(
    "/favorites",
    response_model=SearchResponse,
    tags=["favorites"],
    summary="List favorites",
    description="List a user's favorite recipes. Requires user_id query parameter.",
    operation_id="list_favorites",
)
# PUBLIC_INTERFACE
def list_favorites(
    request,
    user_id: str = Query(..., description="User identifier (lightweight, not authenticated)."),
) -> SearchResponse:
    """List favorite recipes for a user."""
    store = _get_store(request)
    recipes = store.get_favorites(user_id)
    items = [store.recipe_to_summary(r) for r in recipes]
    return SearchResponse(items=items, total=len(items))


@router.post(
    "/favorites/{recipe_id}",
    response_model=Message,
    tags=["favorites"],
    summary="Add favorite",
    description="Mark a recipe as favorite for a given user_id.",
    operation_id="add_favorite",
)
# PUBLIC_INTERFACE
def add_favorite(request, recipe_id: str, body: FavoriteCreate) -> Message:
    """Add a recipe to user's favorites."""
    store = _get_store(request)
    store.set_favorite(user_id=body.user_id, recipe_id=recipe_id, is_favorite=True)
    return Message(message="Favorite saved.")


@router.delete(
    "/favorites/{recipe_id}",
    response_model=Message,
    tags=["favorites"],
    summary="Remove favorite",
    description="Unmark a recipe as favorite for a given user_id (query parameter).",
    operation_id="remove_favorite",
)
# PUBLIC_INTERFACE
def remove_favorite(
    request,
    recipe_id: str,
    user_id: str = Query(..., description="User identifier (lightweight, not authenticated)."),
) -> Message:
    """Remove a recipe from user's favorites."""
    store = _get_store(request)
    store.set_favorite(user_id=user_id, recipe_id=recipe_id, is_favorite=False)
    return Message(message="Favorite removed.")


@router.post(
    "/recipes/{recipe_id}/ratings",
    response_model=Rating,
    tags=["ratings"],
    summary="Create/update rating",
    description="Create or update a user's rating (1-5) for a recipe.",
    operation_id="upsert_rating",
)
# PUBLIC_INTERFACE
def upsert_rating(request, recipe_id: str, body: RatingCreate) -> Rating:
    """Create or update a rating for a recipe."""
    store = _get_store(request)
    return store.upsert_rating(recipe_id=recipe_id, user_id=body.user_id, rating=body.rating)


@router.get(
    "/recipes/{recipe_id}/ratings/me",
    response_model=Optional[Rating],
    tags=["ratings"],
    summary="Get user's rating",
    description="Fetch the requesting user's rating for a recipe (if any).",
    operation_id="get_my_rating",
)
# PUBLIC_INTERFACE
def get_my_rating(
    request,
    recipe_id: str,
    user_id: str = Query(..., description="User identifier (lightweight, not authenticated)."),
) -> Optional[Rating]:
    """Get current user's rating for a recipe, if any."""
    store = _get_store(request)
    return store.get_user_rating(recipe_id=recipe_id, user_id=user_id)
