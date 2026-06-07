from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlmodel import Field, SQLModel


class Recipe(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = Field(default="")
    photo_filename: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Ingredient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    recipe_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("recipe.id", ondelete="CASCADE"), nullable=False
        )
    )
    name: str
    quantity: str = Field(default="")
    unit: str = Field(default="")


class WeekPlan(SQLModel, table=True):
    __tablename__ = "week_plan"  # type: ignore[assignment]
    __table_args__ = (UniqueConstraint("week_start", "day_of_week"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    week_start: str  # ISO date YYYY-MM-DD (always a Monday)
    day_of_week: int  # 0 = Monday … 6 = Sunday
    recipe_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            Integer, ForeignKey("recipe.id", ondelete="SET NULL"), nullable=True
        ),
    )
