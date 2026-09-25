from datetime import date
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas, diet_engine, habit_engine, chat
from .database import engine, get_db

load_dotenv()  # picks up ANTHROPIC_API_KEY from backend/.env if present

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Gym & Fitness Assistant API",
    description="MVP: AI Dietician & Calorie Coach + AI Fitness Habit Tracker",
    version="0.1.0",
)

# Allow the local frontend (or any origin during dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "service": "AI Gym & Fitness Assistant API"}


# ---------- Users ----------

@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ---------- Diet plan ----------

@app.get("/users/{user_id}/diet-plan", response_model=schemas.DietPlanOut)
def get_diet_plan(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = diet_engine.generate_diet_plan(
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        age=user.age,
        sex=user.sex,
        goal=user.goal,
        activity_level=user.activity_level,
    )
    return plan


# ---------- Habit tracker ----------

@app.post("/workouts", response_model=schemas.HabitStatusOut)
def log_workout(entry: schemas.WorkoutLogCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == entry.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    log = models.WorkoutLog(
        user_id=entry.user_id,
        logged_date=entry.logged_date or date.today(),
        note=entry.note,
    )
    db.add(log)
    db.commit()

    return _habit_status(user, db)


@app.get("/users/{user_id}/habit-status", response_model=schemas.HabitStatusOut)
def get_habit_status(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _habit_status(user, db)


def _habit_status(user: models.User, db: Session) -> dict:
    logs = db.query(models.WorkoutLog).filter(models.WorkoutLog.user_id == user.id).all()
    logged_dates = [log.logged_date for log in logs]
    risk = habit_engine.assess_skip_risk(logged_dates, user.expected_weekly_sessions)
    return {
        "total_sessions_logged": len(logged_dates),
        "sessions_last_7_days": risk["sessions_last_7_days"],
        "expected_weekly_sessions": risk["expected_weekly_sessions"],
        "skip_risk": risk["skip_risk"],
        "nudge_message": risk["nudge_message"],
    }


# ---------- Chat (Virtual Gym Buddy / AI Dietician) ----------

@app.post("/chat", response_model=schemas.ChatResponse)
def chat_with_assistant(req: schemas.ChatRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = diet_engine.generate_diet_plan(
        weight_kg=user.weight_kg,
        height_cm=user.height_cm,
        age=user.age,
        sex=user.sex,
        goal=user.goal,
        activity_level=user.activity_level,
    )
    habit_status = _habit_status(user, db)
    reply = chat.get_reply(req.message, plan, habit_status)
    return {"reply": reply}
