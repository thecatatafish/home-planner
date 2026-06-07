from functools import lru_cache

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlmodel import select

from deps import SessionDep, templates
from models import Ingredient
from utils import COMMON_INGREDIENTS

router = APIRouter(prefix="/htmx")


@lru_cache(maxsize=512)
def _suggestions_html(q_lower: str, db_names: tuple[str, ...]) -> str:
    """Build suggestion list HTML. Pure function — safe to cache by (query, db_names)."""
    db_name_set = {n.lower() for n in db_names}
    common_matches = [
        n
        for n in COMMON_INGREDIENTS
        if q_lower in n.lower() and n.lower() not in db_name_set
    ]
    suggestions = (list(db_names) + common_matches)[:10]
    if not suggestions:
        return ""
    items = "\n".join(
        f'<li onclick="selectIngredient(this)">{name}</li>' for name in suggestions
    )
    return f'<ul class="suggestions-list">{items}</ul>'


@router.get("/ingredient-row", response_class=HTMLResponse)
async def ingredient_row(request: Request):
    return templates.TemplateResponse(request, "partials/ingredient_row.html", {})


@router.get("/ingredient-suggestions", response_class=HTMLResponse)
async def ingredient_suggestions(session: SessionDep, q: str = ""):
    q = q.strip()
    if not q:
        return HTMLResponse("")

    q_lower = q.lower()

    db_names: tuple[str, ...] = tuple(
        session.exec(
            select(Ingredient.name)
            .distinct()
            .where(func.lower(Ingredient.name).contains(q_lower))
            .order_by(Ingredient.name)
            .limit(20)
        ).all()
    )

    return HTMLResponse(_suggestions_html(q_lower, db_names))
