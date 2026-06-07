from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlmodel import select

from deps import SessionDep, templates
from models import Recipe, WeekPlan
from utils import build_days, get_week_start

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/planner")


@router.get("/planner", response_class=HTMLResponse)
async def planner_page(
    request: Request, session: SessionDep, week: Optional[str] = None
):
    week_start = get_week_start(week)
    week_str = week_start.isoformat()
    week_end = week_start + timedelta(days=6)

    recipes = session.exec(select(Recipe).order_by(Recipe.name)).all()
    plans = session.exec(select(WeekPlan).where(WeekPlan.week_start == week_str)).all()
    plan_map = {p.day_of_week: p.recipe_id for p in plans}

    return templates.TemplateResponse(
        request,
        "planner.html",
        {
            "days": build_days(session, week_start, plan_map),
            "recipes": recipes,
            "week_start": week_start,
            "week_end": week_end,
            "week_str": week_str,
            "today": date.today(),
            "prev_week": (week_start - timedelta(weeks=1)).isoformat(),
            "next_week": (week_start + timedelta(weeks=1)).isoformat(),
        },
    )


@router.post("/planner/{week_str}/{day}", response_class=HTMLResponse)
async def set_day_plan(
    request: Request,
    week_str: str,
    day: int,
    session: SessionDep,
    recipe_id: str = Form(default=""),
):
    if not 0 <= day <= 6:
        raise HTTPException(status_code=400, detail="Invalid day")

    if recipe_id and recipe_id != "0":
        session.exec(
            sqlite_insert(WeekPlan)
            .values(week_start=week_str, day_of_week=day, recipe_id=int(recipe_id))
            .on_conflict_do_update(
                index_elements=["week_start", "day_of_week"],
                set_={"recipe_id": int(recipe_id)},
            )
        )
    else:
        plan = session.exec(
            select(WeekPlan).where(
                WeekPlan.week_start == week_str, WeekPlan.day_of_week == day
            )
        ).first()
        if plan:
            session.delete(plan)

    session.commit()

    week_start = date.fromisoformat(week_str)
    plan_map = {day: int(recipe_id)} if recipe_id and recipe_id != "0" else {}
    recipes = session.exec(select(Recipe).order_by(Recipe.name)).all()

    return templates.TemplateResponse(
        request,
        "partials/day_slot.html",
        {
            "day": build_days(session, week_start, plan_map)[day],
            "recipes": recipes,
            "week_str": week_str,
            "today": date.today(),
        },
    )
