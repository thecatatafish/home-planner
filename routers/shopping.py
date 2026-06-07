from collections import defaultdict
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlmodel import select

from deps import SessionDep, templates
from models import Ingredient, Recipe, WeekPlan
from utils import get_week_start

router = APIRouter()


@router.get("/shopping-list", response_class=HTMLResponse)
async def shopping_list(
    request: Request, session: SessionDep, week: Optional[str] = None
):
    week_start = get_week_start(week)
    week_str = week_start.isoformat()
    week_end = week_start + timedelta(days=6)

    rows = session.exec(
        select(
            Recipe.name.label("recipe_name"),
            Ingredient.name.label("ingredient_name"),
            Ingredient.quantity,
            Ingredient.unit,
        )
        .select_from(WeekPlan)
        .join(Recipe, Recipe.id == WeekPlan.recipe_id)
        .outerjoin(Ingredient, Ingredient.recipe_id == Recipe.id)
        .where(WeekPlan.week_start == week_str)
        .order_by(Recipe.name, Ingredient.name)
    ).all()

    grouped: dict[str, list] = defaultdict(list)
    for row in rows:
        if not row.ingredient_name:
            continue
        key = row.ingredient_name.strip().lower()
        grouped[key].append(
            {
                "name": row.ingredient_name,
                "quantity": row.quantity or "",
                "unit": row.unit or "",
                "recipe": row.recipe_name,
            }
        )

    return templates.TemplateResponse(
        request,
        "shopping_list.html",
        {
            "week_start": week_start,
            "week_end": week_end,
            "week_str": week_str,
            "sorted_ingredients": sorted(grouped.items()),
            "prev_week": (week_start - timedelta(weeks=1)).isoformat(),
            "next_week": (week_start + timedelta(weeks=1)).isoformat(),
            "has_items": bool(grouped),
        },
    )
