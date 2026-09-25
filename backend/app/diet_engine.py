"""
Rules-based diet/calorie engine.
Deliberately deterministic (no LLM) so numbers are always accurate and reproducible.
The chatbot layer (chat.py) explains these numbers in natural language.
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_CALORIE_ADJUSTMENT = {
    "cut": -500,
    "maintain": 0,
    "bulk": 300,
}

GOAL_MACRO_SPLIT = {
    # protein / carbs / fat as % of total calories
    "cut": {"protein": 0.40, "carbs": 0.35, "fat": 0.25},
    "maintain": {"protein": 0.30, "carbs": 0.40, "fat": 0.30},
    "bulk": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
}


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Mifflin-St Jeor Equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return round(base + (5 if sex.lower() == "male" else -161), 1)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    multiplier = ACTIVITY_MULTIPLIERS.get(activity_level, 1.375)
    return round(bmr * multiplier, 1)


def calculate_macros(target_calories: float, goal: str) -> dict:
    split = GOAL_MACRO_SPLIT.get(goal, GOAL_MACRO_SPLIT["maintain"])
    return {
        "protein_g": round(target_calories * split["protein"] / 4, 1),  # 4 kcal/g
        "carbs_g": round(target_calories * split["carbs"] / 4, 1),      # 4 kcal/g
        "fat_g": round(target_calories * split["fat"] / 9, 1),          # 9 kcal/g
    }


def suggest_meals(goal: str) -> list:
    library = {
        "cut": [
            "Breakfast: Greek yogurt, berries, chia seeds",
            "Lunch: Grilled chicken breast, quinoa, steamed broccoli",
            "Dinner: Baked fish, large mixed salad, olive oil dressing",
            "Snack: Boiled eggs or a protein shake",
        ],
        "maintain": [
            "Breakfast: Oats, banana, peanut butter",
            "Lunch: Turkey/paneer wrap, brown rice, vegetables",
            "Dinner: Lean meat or lentils, sweet potato, greens",
            "Snack: Mixed nuts and fruit",
        ],
        "bulk": [
            "Breakfast: Whole eggs, oats, whole milk, banana",
            "Lunch: Chicken/paneer, rice, ghee, dal",
            "Dinner: Beef/soy chunks, pasta or rice, vegetables",
            "Snack: Peanut butter sandwich or mass-gainer shake",
        ],
    }
    return library.get(goal, library["maintain"])


def build_grocery_list(goal: str) -> list:
    library = {
        "cut": ["Chicken breast", "Greek yogurt", "Eggs", "Broccoli", "Spinach",
                "Quinoa", "Berries", "Olive oil", "Fish", "Chia seeds"],
        "maintain": ["Oats", "Bananas", "Peanut butter", "Brown rice", "Turkey/paneer",
                     "Mixed vegetables", "Lentils", "Sweet potato", "Nuts", "Fruit"],
        "bulk": ["Whole eggs", "Whole milk", "Oats", "Chicken/paneer", "Rice",
                 "Ghee", "Dal", "Pasta", "Peanut butter", "Mass gainer (optional)"],
    }
    return library.get(goal, library["maintain"])


def generate_diet_plan(weight_kg, height_cm, age, sex, goal, activity_level) -> dict:
    bmi = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, sex)
    tdee = calculate_tdee(bmr, activity_level)
    target_calories = round(tdee + GOAL_CALORIE_ADJUSTMENT.get(goal, 0), 1)

    return {
        "bmi": bmi,
        "bmi_category": bmi_category(bmi),
        "bmr": bmr,
        "tdee": tdee,
        "target_calories": target_calories,
        "macros": calculate_macros(target_calories, goal),
        "meal_suggestions": suggest_meals(goal),
        "grocery_list": build_grocery_list(goal),
    }
