from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)          # "male" | "female"
    height_cm = Column(Float, nullable=False)
    weight_kg = Column(Float, nullable=False)
    goal = Column(String, nullable=False)          # "cut" | "maintain" | "bulk"
    activity_level = Column(String, nullable=False)  # "sedentary"|"light"|"moderate"|"active"|"very_active"
    expected_weekly_sessions = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)

    workouts = relationship("WorkoutLog", back_populates="user")


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    logged_date = Column(Date, default=date.today)
    note = Column(String, nullable=True)

    user = relationship("User", back_populates="workouts")
