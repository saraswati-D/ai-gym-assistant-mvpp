"""
Rules-based habit / skip-risk engine.
MVP version uses simple pattern rules instead of a trained ML model —
easy to upgrade later (see README) once you have enough logged data.
"""
from datetime import date, timedelta
from typing import List


def sessions_in_last_n_days(logged_dates: List[date], n: int) -> int:
    cutoff = date.today() - timedelta(days=n)
    return sum(1 for d in logged_dates if d >= cutoff)


def assess_skip_risk(logged_dates: List[date], expected_weekly_sessions: int) -> dict:
    recent = sessions_in_last_n_days(logged_dates, 7)

    if expected_weekly_sessions <= 0:
        expected_weekly_sessions = 1

    ratio = recent / expected_weekly_sessions

    if ratio >= 0.8:
        risk = "low"
        nudge = "Nice consistency this week — keep the streak going!"
    elif ratio >= 0.4:
        risk = "medium"
        nudge = "You've slowed down a bit this week. A quick 20-minute session today keeps momentum."
    else:
        risk = "high"
        nudge = "You've missed most of your sessions this week. Let's reset — even a short walk counts as a win today."

    return {
        "sessions_last_7_days": recent,
        "expected_weekly_sessions": expected_weekly_sessions,
        "skip_risk": risk,
        "nudge_message": nudge,
    }
