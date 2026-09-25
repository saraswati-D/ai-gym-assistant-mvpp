# AI Gym & Fitness Assistant — MVP

A working slice of the full 7-module concept from the original project proposal.
This MVP implements **two modules end-to-end**:

1. **AI Dietician & Calorie Coach** — BMI/BMR/TDEE calculation, macro breakdown, meal suggestions, grocery list, and a conversational chat layer.
2. **AI Fitness Habit Tracker** — workout logging with rule-based skip-risk detection and motivational nudges.

The other 5 modules from the original brief (AI Gym Trainer / pose detection, Smart Gym IoT integration, Virtual Gym Buddy sentiment analysis, Pose-to-Performance Analyzer, Gym Recommender) are documented below as a **roadmap** — they need computer vision, IoT hardware, or larger datasets that go beyond an MVP.

---

## Why this scope

The original proposal is a 7-module system spanning computer vision, IoT, and conversational AI — a multi-person, multi-month build. This MVP deliberately picks the two modules that:
- Need no hardware (no camera, no smart gym equipment)
- Can be fully rules-based first (accurate, testable, no model training required)
- Still demonstrate the "AI ecosystem" concept end-to-end: data in → personalized output → conversational access

## Project structure

```
ai-gym-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes
│   │   ├── models.py        # SQLAlchemy ORM models (User, WorkoutLog)
│   │   ├── schemas.py       # Pydantic request/response schemas
│   │   ├── database.py      # DB session setup (SQLite by default)
│   │   ├── diet_engine.py   # BMI/BMR/TDEE/macro calculation (rules-based)
│   │   ├── habit_engine.py  # Skip-risk detection (rules-based)
│   │   └── chat.py          # Conversational layer over the two engines
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── index.html            # Single-page dashboard (vanilla JS, no build step)
```

## Running it

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
uvicorn app.main:app --reload
```

This starts the API at `http://localhost:8000`. Interactive API docs are auto-generated at `http://localhost:8000/docs`.

### Frontend

Just open `frontend/index.html` directly in a browser (or serve it with `python3 -m http.server` from the `frontend/` folder). It talks to the backend at `http://localhost:8000` — make sure that's running first.

## API overview

| Method | Endpoint                          | Purpose                              |
|--------|------------------------------------|---------------------------------------|
| POST   | `/users`                          | Create a user profile                 |
| GET    | `/users/{id}`                     | Get a user profile                    |
| GET    | `/users/{id}/diet-plan`           | Get calculated diet plan              |
| POST   | `/workouts`                       | Log a workout session                 |
| GET    | `/users/{id}/habit-status`        | Get skip-risk + streak status         |
| POST   | `/chat`                           | Chat with the AI coach                |

## Design decisions worth knowing

- **Diet numbers are rules-based, not LLM-generated.** BMI/BMR (Mifflin-St Jeor)/TDEE/macros are deterministic formulas. This keeps the numbers accurate and testable. The chat layer (`chat.py`) explains these numbers in natural language — it doesn't compute them.
- **Habit tracking uses simple pattern rules**, not a trained ML model, since you won't have enough logged data early on to train anything meaningful. `habit_engine.py` is isolated specifically so you can swap in a real model later without touching the API layer.
- **SQLite by default.** Swap the connection string in `database.py` for Postgres/MySQL later — no other code changes needed.

## Roadmap: the other 5 modules

| Module | What it needs | Suggested next step |
|---|---|---|
| AI Gym Trainer (pose/rep detection) | Camera input, MediaPipe/OpenPose | Prototype separately as a webcam script before integrating |
| Smart Gym Assistant (IoT) | Actual IoT-enabled equipment or simulators | Needs hardware access — out of scope without it |
| Virtual Gym Buddy (sentiment) | Larger conversational dataset or LLM API key | Extend `chat.py` to call a real LLM, passing plan/habit data as context |
| Pose-to-Performance Analyzer | Depends on Gym Trainer module above | Build after pose detection is working |
| Gym Recommender & Planner | Location data + gym database/API | Integrate a places API (e.g. Google Places) once core MVP is stable |

## Chat: LLM-powered with automatic fallback

`chat.py` now calls Claude (Anthropic API) for natural conversational replies, grounded in the real diet plan and habit-status numbers so it never invents figures. **No API key needed to run the project** — if `ANTHROPIC_API_KEY` isn't set, it automatically falls back to the original deterministic keyword-based replies, so the app always works out of the box.

To enable the LLM path:
1. Copy `backend/.env.example` to `backend/.env`
2. Add your key: `ANTHROPIC_API_KEY=sk-ant-...`
3. Restart the backend — chat replies will now come from Claude instead of the fallback rules

If the API call ever fails (bad key, rate limit, network issue), it silently falls back to the rule-based reply rather than breaking the chat.
