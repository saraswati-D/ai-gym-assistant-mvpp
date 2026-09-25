from datetime import date
from typing import Optional, List
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str
    age: int = Field(gt=0, lt=120)
    sex: str  # "male" | "female"
    height_cm: float = Field(gt=0)
    weight_kg: float = Field(gt=0)
    goal: str  # "cut" | "maintain" | "bulk"
    activity_level: str  # "sedentary"|"light"|"moderate"|"active"|"very_active"
    expected_weekly_sessions: int = 3


class UserOut(UserCreate):
    id: int

    class Config:
        from_attributes = True


class DietPlanOut(BaseModel):
    bmi: float
    bmi_category: str
    bmr: float
    tdee: float
    target_calories: float
    macros: dict
    meal_suggestions: List[str]
    grocery_list: List[str]


class WorkoutLogCreate(BaseModel):
    user_id: int
    logged_date: Optional[date] = None
    note: Optional[str] = None


class HabitStatusOut(BaseModel):
    total_sessions_logged: int
    sessions_last_7_days: int
    expected_weekly_sessions: int
    skip_risk: str  # "low" | "medium" | "high"
    nudge_message: str


class ChatRequest(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
