from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    """Enumeration for recipe difficulty."""

    easy = "easy"
    medium = "medium"
    hard = "hard"


class Category(BaseModel):
    """A recipe category (e.g., Breakfast, Dinner)."""

    id: str = Field(..., description="Stable unique identifier for the category.")
    name: str = Field(..., description="Human readable category name.")
    description: Optional[str] = Field(
        default=None, description="Optional short description of the category."
    )


class RecipeSummary(BaseModel):
    """Small representation of a recipe used in list and grid views."""

    id: str = Field(..., description="Stable unique identifier for the recipe.")
    title: str = Field(..., description="Recipe title.")
    category_id: str = Field(..., description="Category id this recipe belongs to.")
    image_url: Optional[str] = Field(
        default=None,
        description="Optional image URL. If absent, frontend should show a placeholder.",
    )
    avg_rating: float = Field(
        0.0,
        ge=0,
        le=5,
        description="Average rating (0-5) derived from all user ratings.",
    )
    rating_count: int = Field(0, ge=0, description="Number of ratings recorded.")


class Recipe(BaseModel):
    """Full recipe representation."""

    id: str = Field(..., description="Stable unique identifier for the recipe.")
    title: str = Field(..., description="Recipe title.")
    description: str = Field(..., description="Short description of the recipe.")
    category_id: str = Field(..., description="Category id this recipe belongs to.")
    ingredients: List[str] = Field(
        default_factory=list, description="List of ingredients."
    )
    instructions: List[str] = Field(
        default_factory=list, description="Step-by-step cooking instructions."
    )
    prep_minutes: int = Field(..., ge=0, description="Estimated prep time in minutes.")
    cook_minutes: int = Field(..., ge=0, description="Estimated cook time in minutes.")
    difficulty: Difficulty = Field(..., description="Recipe difficulty level.")
    image_url: Optional[str] = Field(
        default=None,
        description="Optional image URL. If absent, frontend should show a placeholder.",
    )
    avg_rating: float = Field(
        0.0,
        ge=0,
        le=5,
        description="Average rating (0-5) derived from all user ratings.",
    )
    rating_count: int = Field(0, ge=0, description="Number of ratings recorded.")


class RatingCreate(BaseModel):
    """Request payload to create/update a user's rating for a recipe."""

    user_id: str = Field(..., description="User identifier (lightweight, not authenticated).")
    rating: int = Field(..., ge=1, le=5, description="Rating value 1-5.")


class Rating(BaseModel):
    """A stored rating."""

    recipe_id: str = Field(..., description="Recipe id being rated.")
    user_id: str = Field(..., description="User id who created the rating.")
    rating: int = Field(..., ge=1, le=5, description="Rating value 1-5.")


class FavoriteCreate(BaseModel):
    """Request payload to favorite/unfavorite a recipe."""

    user_id: str = Field(..., description="User identifier (lightweight, not authenticated).")


class Favorite(BaseModel):
    """A stored favorite mapping."""

    user_id: str = Field(..., description="User identifier.")
    recipe_id: str = Field(..., description="Recipe identifier.")


class SearchResponse(BaseModel):
    """Response for recipe listing and search endpoints."""

    items: List[RecipeSummary] = Field(..., description="List of recipe summaries.")
    total: int = Field(..., ge=0, description="Total number of results returned.")


class Message(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Human readable message.")
