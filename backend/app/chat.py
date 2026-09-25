"""
Conversational layer for the AI Dietician & Virtual Gym Buddy.

Design choice: this does NOT compute numbers itself. It takes the
already-computed diet plan / habit status (from diet_engine.py / habit_engine.py)
as ground truth and turns it into a natural-language reply. This keeps the
numbers accurate no matter which reply path below is used.

Two reply paths:
  - rule_based_reply(): deterministic keyword matching. Always works, no API key needed.
  - llm_reply(): calls Anthropic's Claude API, grounded in the same plan/status data,
    so responses are more natural and can handle messages the keyword rules can't.

get_reply() picks whichever is available: LLM if ANTHROPIC_API_KEY is set, otherwise
falls back to rule_based_reply() automatically. This means the project runs out of
the box with zero API keys, and upgrades automatically once you add one.
"""
import os

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


SYSTEM_PROMPT = """You are a friendly, encouraging AI fitness coach inside a gym app \
(the "Virtual Gym Buddy" / "AI Dietician" module). You are given the user's already-\
calculated diet plan and habit-tracking status as ground-truth data below. Answer the \
user's message using ONLY the numbers provided — never invent or recalculate calorie, \
macro, BMI, or workout figures yourself. Keep replies short (2-4 sentences), warm, and \
conversational, like a supportive trainer texting a client. If the user's message isn't \
related to diet or workouts, gently redirect them to what you can help with."""


def get_reply(message: str, plan: dict, habit_status: dict) -> str:
    """Main entry point used by the API layer. Picks LLM or rule-based automatically."""
    if _ANTHROPIC_AVAILABLE and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return llm_reply(message, plan, habit_status)
        except Exception:
            # If the API call fails for any reason (bad key, network, rate limit),
            # don't break the chat — fall back to the deterministic version.
            return rule_based_reply(message, plan, habit_status)
    return rule_based_reply(message, plan, habit_status)


def llm_reply(message: str, plan: dict, habit_status: dict) -> str:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env automatically

    context = (
        f"USER'S DIET PLAN:\n"
        f"- BMI: {plan['bmi']} ({plan['bmi_category']})\n"
        f"- BMR: {plan['bmr']} kcal | Maintenance (TDEE): {plan['tdee']} kcal\n"
        f"- Daily target: {plan['target_calories']} kcal\n"
        f"- Macros: {plan['macros']['protein_g']}g protein, "
        f"{plan['macros']['carbs_g']}g carbs, {plan['macros']['fat_g']}g fat\n"
        f"- Sample meals: {'; '.join(plan['meal_suggestions'])}\n"
        f"- Grocery list: {', '.join(plan['grocery_list'])}\n\n"
        f"USER'S HABIT STATUS:\n"
        f"- Sessions this week: {habit_status['sessions_last_7_days']} of "
        f"{habit_status['expected_weekly_sessions']} expected\n"
        f"- Total sessions logged all-time: {habit_status['total_sessions_logged']}\n"
        f"- Skip risk: {habit_status['skip_risk']}\n\n"
        f"USER'S MESSAGE: {message}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": context}],
    )
    return response.content[0].text.strip()


def rule_based_reply(message: str, plan: dict, habit_status: dict) -> str:
    msg = message.lower()

    # Weight loss / weight gain / "will this work" style questions
    weight_words = ["weight", "wieght", "wight", "fat loss", "fatloss"]
    goal_verbs = ["lose", "loose", "gain", "reduce", "cut", "build", "increase"]
    if (any(w in msg for w in weight_words) and any(v in msg for v in goal_verbs)) or \
       any(p in msg for p in ["is it possible", "will i", "can i lose", "how do i lose", "build muscle"]):
        return (
            f"Yes — based on your numbers, eating around {plan['target_calories']} kcal/day "
            f"(vs your maintenance of {plan['tdee']} kcal) is set up to support that. "
            f"Consistency with both diet and your workout sessions matters more than any single day. "
            f"Stick with the plan and check back on your habit tracker to see your progress."
        )

    if any(w in msg for w in ["calorie", "how much should i eat", "intake", "how many calories"]):
        return (
            f"Your estimated daily target is {plan['target_calories']} kcal "
            f"(maintenance is {plan['tdee']} kcal, adjusted for your goal). "
            f"That breaks down to roughly {plan['macros']['protein_g']}g protein, "
            f"{plan['macros']['carbs_g']}g carbs, and {plan['macros']['fat_g']}g fat."
        )

    if any(w in msg for w in ["bmi", "body mass"]):
        return f"Your BMI is {plan['bmi']}, which falls in the '{plan['bmi_category']}' range."

    if any(w in msg for w in ["meal", "eat today", "food", "what to eat", "what should i eat"]):
        meals = "; ".join(plan["meal_suggestions"])
        return f"Here's a sample day: {meals}."

    if any(w in msg for w in ["grocery", "shopping", "buy"]):
        items = ", ".join(plan["grocery_list"])
        return f"Your grocery list: {items}."

    if any(w in msg for w in ["workout", "skip", "session", "motivat", "streak"]):
        return (
            f"You've logged {habit_status['sessions_last_7_days']} of your "
            f"{habit_status['expected_weekly_sessions']} expected sessions this week. "
            f"{habit_status['nudge_message']}"
        )

    return (
        "I can help with your calories, macros, meal plan, grocery list, or workout "
        "streak — just ask, e.g. 'how many calories should I eat?' or 'what should I eat today?'"
    )
