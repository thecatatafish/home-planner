import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlmodel import Session, select

from config import settings
from models import Ingredient, Recipe

DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _load_ingredients(path: Path) -> list[str]:
    seen: set[str] = set()
    result = []
    for line in path.read_text(encoding="utf-8").splitlines():
        name = line.strip()
        if name and not name.startswith("#"):
            key = name.lower()
            if key not in seen:
                seen.add(key)
                result.append(name)
    return sorted(result, key=str.casefold)


COMMON_INGREDIENTS = _load_ingredients(Path("ingredients.txt"))


def get_week_start(week_str: Optional[str] = None) -> date:
    if week_str:
        try:
            d = date.fromisoformat(week_str)
            return d - timedelta(days=d.weekday())
        except ValueError:
            pass
    today = date.today()
    return today - timedelta(days=today.weekday())


async def save_photo(upload: Optional[UploadFile]) -> Optional[str]:
    if not upload or not upload.filename:
        return None
    ext = Path(upload.filename).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        return None
    content = await upload.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413, detail=f"Photo exceeds {settings.max_upload_mb} MB limit"
        )
    filename = f"{uuid.uuid4()}{ext}"
    (settings.upload_dir / filename).write_bytes(content)
    return filename


def delete_photo(filename: str) -> None:
    path = settings.upload_dir / filename
    if path.exists():
        path.unlink()


def add_ingredients(
    session: Session,
    recipe_id: int,
    names: list[str],
    quantities: list[str],
    units: list[str],
) -> None:
    for i, name in enumerate(names):
        name = name.strip()
        if not name:
            continue
        session.add(
            Ingredient(
                recipe_id=recipe_id,
                name=name,
                quantity=quantities[i].strip() if i < len(quantities) else "",
                unit=units[i].strip() if i < len(units) else "",
            )
        )


def build_days(
    session: Session, week_start: date, plan_map: dict[int, int]
) -> list[dict]:
    """Return 7 day-slot dicts for the given week. Batch-loads recipes in one query."""
    recipe_ids = [rid for rid in plan_map.values() if rid]
    recipes_by_id: dict[int, Recipe] = {}
    if recipe_ids:
        rows = session.exec(select(Recipe).where(Recipe.id.in_(recipe_ids))).all()
        recipes_by_id = {r.id: r for r in rows}

    return [
        {
            "index": i,
            "name": DAY_NAMES[i],
            "date": week_start + timedelta(days=i),
            "recipe": recipes_by_id.get(plan_map.get(i)),
            "recipe_id": plan_map.get(i),
        }
        for i in range(7)
    ]
