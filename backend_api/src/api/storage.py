from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from fastapi import HTTPException, status

from src.api.models import Category, Difficulty, Rating, Recipe, RecipeSummary

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DATA_FILE = os.path.join(DATA_DIR, "store.json")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _safe_read_json(path: str) -> Optional[dict]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Corrupt or partially written file; ignore and rebuild from defaults.
        return None


def _safe_write_json(path: str, payload: dict) -> None:
    _ensure_data_dir()
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def _default_categories() -> List[Category]:
    return [
        Category(id="breakfast", name="Breakfast", description="Start your day right."),
        Category(id="lunch", name="Lunch", description="Quick and satisfying midday meals."),
        Category(id="dinner", name="Dinner", description="Hearty meals for the evening."),
        Category(id="dessert", name="Dessert", description="Sweet treats and indulgences."),
        Category(id="snack", name="Snack", description="Light bites anytime."),
    ]


def _default_recipes() -> List[Recipe]:
    # Note: images are optional; keep URLs empty to avoid external dependency.
    return [
        Recipe(
            id="r1",
            title="Avocado Toast",
            description="Creamy avocado on toasted bread with a bright, lemony finish.",
            category_id="breakfast",
            ingredients=["bread", "avocado", "lemon", "salt", "pepper", "chili flakes"],
            instructions=[
                "Toast the bread.",
                "Mash avocado with lemon, salt, and pepper.",
                "Spread avocado on toast and top with chili flakes.",
            ],
            prep_minutes=5,
            cook_minutes=3,
            difficulty=Difficulty.easy,
            image_url=None,
        ),
        Recipe(
            id="r2",
            title="Greek Salad",
            description="Crisp vegetables with feta and a simple olive oil dressing.",
            category_id="lunch",
            ingredients=[
                "cucumber",
                "tomato",
                "red onion",
                "feta",
                "olives",
                "olive oil",
                "oregano",
                "salt",
                "pepper",
            ],
            instructions=[
                "Chop vegetables into bite-size pieces.",
                "Toss with olives and crumbled feta.",
                "Dress with olive oil, oregano, salt, and pepper.",
            ],
            prep_minutes=10,
            cook_minutes=0,
            difficulty=Difficulty.easy,
            image_url=None,
        ),
        Recipe(
            id="r3",
            title="One-Pan Lemon Garlic Chicken",
            description="Juicy chicken thighs roasted with lemon and garlic.",
            category_id="dinner",
            ingredients=["chicken thighs", "lemon", "garlic", "olive oil", "salt", "pepper"],
            instructions=[
                "Preheat oven to 425°F (220°C).",
                "Season chicken with salt and pepper.",
                "Add garlic and lemon slices; drizzle with olive oil.",
                "Roast for 30-35 minutes until cooked through.",
            ],
            prep_minutes=10,
            cook_minutes=35,
            difficulty=Difficulty.medium,
            image_url=None,
        ),
        Recipe(
            id="r4",
            title="Chocolate Yogurt Parfait",
            description="A layered dessert-like parfait that's still light and refreshing.",
            category_id="dessert",
            ingredients=["greek yogurt", "cocoa powder", "honey", "granola", "berries"],
            instructions=[
                "Mix yogurt with cocoa powder and honey.",
                "Layer yogurt with granola and berries in a glass.",
                "Serve immediately.",
            ],
            prep_minutes=7,
            cook_minutes=0,
            difficulty=Difficulty.easy,
            image_url=None,
        ),
        Recipe(
            id="r5",
            title="Hummus & Veggie Plate",
            description="A quick snack plate with crunchy vegetables and creamy hummus.",
            category_id="snack",
            ingredients=["hummus", "carrots", "cucumber", "bell pepper", "pita"],
            instructions=[
                "Slice vegetables.",
                "Arrange with hummus and pita.",
                "Enjoy.",
            ],
            prep_minutes=8,
            cook_minutes=0,
            difficulty=Difficulty.easy,
            image_url=None,
        ),
    ]


@dataclass
class Store:
    """Simple persistence layer backed by a JSON file."""

    categories: Dict[str, Category]
    recipes: Dict[str, Recipe]
    # favorites are user_id -> set(recipe_id)
    favorites: Dict[str, Set[str]]
    # ratings are (recipe_id, user_id) -> rating_int
    ratings: Dict[Tuple[str, str], int]

    @staticmethod
    def load() -> "Store":
        payload = _safe_read_json(DATA_FILE)
        if not payload:
            categories_list = _default_categories()
            recipes_list = _default_recipes()
            store = Store(
                categories={c.id: c for c in categories_list},
                recipes={r.id: r for r in recipes_list},
                favorites={},
                ratings={},
            )
            store.save()
            return store

        categories = {c["id"]: Category(**c) for c in payload.get("categories", [])}
        recipes = {r["id"]: Recipe(**r) for r in payload.get("recipes", [])}

        favorites_payload = payload.get("favorites", {})
        favorites: Dict[str, Set[str]] = {
            user_id: set(recipe_ids) for user_id, recipe_ids in favorites_payload.items()
        }

        ratings_payload = payload.get("ratings", [])
        ratings: Dict[Tuple[str, str], int] = {}
        for item in ratings_payload:
            recipe_id = item.get("recipe_id")
            user_id = item.get("user_id")
            rating = item.get("rating")
            if recipe_id and user_id and isinstance(rating, int):
                ratings[(recipe_id, user_id)] = rating

        return Store(categories=categories, recipes=recipes, favorites=favorites, ratings=ratings)

    def save(self) -> None:
        payload = {
            "categories": [c.model_dump() for c in self.categories.values()],
            "recipes": [r.model_dump() for r in self.recipes.values()],
            "favorites": {u: sorted(list(ids)) for u, ids in self.favorites.items()},
            "ratings": [
                {"recipe_id": rid, "user_id": uid, "rating": rating}
                for (rid, uid), rating in self.ratings.items()
            ],
        }
        _safe_write_json(DATA_FILE, payload)

    def _compute_recipe_aggregate(self, recipe_id: str) -> Tuple[float, int]:
        values = [v for (rid, _uid), v in self.ratings.items() if rid == recipe_id]
        if not values:
            return 0.0, 0
        return float(sum(values)) / len(values), len(values)

    def recipe_to_summary(self, recipe: Recipe) -> RecipeSummary:
        avg, count = self._compute_recipe_aggregate(recipe.id)
        return RecipeSummary(
            id=recipe.id,
            title=recipe.title,
            category_id=recipe.category_id,
            image_url=recipe.image_url,
            avg_rating=avg,
            rating_count=count,
        )

    def recipe_to_full(self, recipe: Recipe) -> Recipe:
        avg, count = self._compute_recipe_aggregate(recipe.id)
        # Return a copy with computed fields filled in
        return Recipe(**{**recipe.model_dump(), "avg_rating": avg, "rating_count": count})

    def get_recipe_or_404(self, recipe_id: str) -> Recipe:
        recipe = self.recipes.get(recipe_id)
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipe '{recipe_id}' not found.",
            )
        return recipe

    def get_category_or_404(self, category_id: str) -> Category:
        category = self.categories.get(category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{category_id}' not found.",
            )
        return category

    def list_recipes(
        self,
        category_id: Optional[str] = None,
        q: Optional[str] = None,
        ingredients: Optional[List[str]] = None,
    ) -> List[Recipe]:
        recipes = list(self.recipes.values())
        if category_id:
            recipes = [r for r in recipes if r.category_id == category_id]

        if q:
            q_low = q.lower().strip()
            if q_low:
                recipes = [
                    r
                    for r in recipes
                    if q_low in r.title.lower() or q_low in r.description.lower()
                ]

        if ingredients:
            normalized = [i.strip().lower() for i in ingredients if i.strip()]
            if normalized:
                recipes = [
                    r
                    for r in recipes
                    if all(
                        any(needle in ing.lower() for ing in r.ingredients)
                        for needle in normalized
                    )
                ]

        # stable ordering: title
        recipes.sort(key=lambda r: r.title.lower())
        return recipes

    def set_favorite(self, user_id: str, recipe_id: str, is_favorite: bool) -> None:
        self.get_recipe_or_404(recipe_id)
        current = self.favorites.setdefault(user_id, set())
        if is_favorite:
            current.add(recipe_id)
        else:
            current.discard(recipe_id)
        self.save()

    def get_favorites(self, user_id: str) -> List[Recipe]:
        ids = sorted(list(self.favorites.get(user_id, set())))
        return [self.recipes[rid] for rid in ids if rid in self.recipes]

    def upsert_rating(self, recipe_id: str, user_id: str, rating: int) -> Rating:
        self.get_recipe_or_404(recipe_id)
        self.ratings[(recipe_id, user_id)] = rating
        self.save()
        return Rating(recipe_id=recipe_id, user_id=user_id, rating=rating)

    def get_user_rating(self, recipe_id: str, user_id: str) -> Optional[Rating]:
        self.get_recipe_or_404(recipe_id)
        value = self.ratings.get((recipe_id, user_id))
        if value is None:
            return None
        return Rating(recipe_id=recipe_id, user_id=user_id, rating=value)
