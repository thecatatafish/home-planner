from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlmodel import delete, select

from deps import SessionDep, templates
from models import Ingredient, Recipe
from utils import add_ingredients, delete_photo, save_photo

router = APIRouter()


@router.get("/recipes", response_class=HTMLResponse)
async def recipes_page(request: Request, session: SessionDep):
    rows = session.exec(
        select(
            Recipe.id,
            Recipe.name,
            Recipe.description,
            Recipe.photo_filename,
            Recipe.created_at,
            func.count(Ingredient.id).label("ingredient_count"),
        )
        .outerjoin(Ingredient, Ingredient.recipe_id == Recipe.id)
        .group_by(Recipe.id)
        .order_by(Recipe.name)
    ).all()
    return templates.TemplateResponse(request, "recipes.html", {"recipes": rows})


@router.get("/recipes/new", response_class=HTMLResponse)
async def new_recipe_page(request: Request):
    return templates.TemplateResponse(
        request, "recipe_form.html", {"recipe": None, "ingredients": []}
    )


@router.post("/recipes", response_class=HTMLResponse)
async def create_recipe(
    session: SessionDep,
    name: str = Form(...),
    description: str = Form(default=""),
    photo: Optional[UploadFile] = File(default=None),
    ingredient_name: list[str] = Form(default=[]),
    ingredient_quantity: list[str] = Form(default=[]),
    ingredient_unit: list[str] = Form(default=[]),
):
    recipe = Recipe(
        name=name.strip(),
        description=description.strip(),
        photo_filename=await save_photo(photo),
    )
    session.add(recipe)
    session.flush()
    add_ingredients(
        session, recipe.id, ingredient_name, ingredient_quantity, ingredient_unit
    )
    session.commit()
    return RedirectResponse(url=f"/recipes/{recipe.id}", status_code=303)


@router.get("/recipes/{recipe_id}", response_class=HTMLResponse)
async def recipe_detail(request: Request, recipe_id: int, session: SessionDep):
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    ingredients = session.exec(
        select(Ingredient)
        .where(Ingredient.recipe_id == recipe_id)
        .order_by(Ingredient.id)
    ).all()
    return templates.TemplateResponse(
        request, "recipe_detail.html", {"recipe": recipe, "ingredients": ingredients}
    )


@router.get("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
async def edit_recipe_page(request: Request, recipe_id: int, session: SessionDep):
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    ingredients = session.exec(
        select(Ingredient)
        .where(Ingredient.recipe_id == recipe_id)
        .order_by(Ingredient.id)
    ).all()
    return templates.TemplateResponse(
        request, "recipe_form.html", {"recipe": recipe, "ingredients": ingredients}
    )


@router.post("/recipes/{recipe_id}/edit", response_class=HTMLResponse)
async def update_recipe(
    recipe_id: int,
    session: SessionDep,
    name: str = Form(...),
    description: str = Form(default=""),
    photo: Optional[UploadFile] = File(default=None),
    ingredient_name: list[str] = Form(default=[]),
    ingredient_quantity: list[str] = Form(default=[]),
    ingredient_unit: list[str] = Form(default=[]),
):
    recipe = session.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    new_photo = await save_photo(photo)
    if new_photo and recipe.photo_filename:
        delete_photo(recipe.photo_filename)
    recipe.name = name.strip()
    recipe.description = description.strip()
    recipe.photo_filename = new_photo or recipe.photo_filename
    session.exec(delete(Ingredient).where(Ingredient.recipe_id == recipe_id))
    add_ingredients(
        session, recipe_id, ingredient_name, ingredient_quantity, ingredient_unit
    )
    session.commit()
    return RedirectResponse(url=f"/recipes/{recipe_id}", status_code=303)


@router.post("/recipes/{recipe_id}/delete", response_class=HTMLResponse)
async def delete_recipe(recipe_id: int, session: SessionDep):
    recipe = session.get(Recipe, recipe_id)
    if recipe:
        if recipe.photo_filename:
            delete_photo(recipe.photo_filename)
        session.delete(recipe)
        session.commit()
    return RedirectResponse(url="/recipes", status_code=303)
