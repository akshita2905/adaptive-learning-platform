# AI-Based Personalized Learning Path Generator

Full-stack application that builds **personalized learning roadmaps** from your skills, career goal, experience level, and daily study time. The backend uses **FastAPI**, **MongoDB**, and **scikit-learn** (TF–IDF + cosine similarity) for content-based recommendations, with an optional **RandomForest / MLP** classifier when experience level is omitted. The frontend is **React (Vite)** with **Tailwind CSS** and **Axios**.

## Features

- User registration and login (JWT)
- `POST /generate-path` — TF–IDF match to a role catalog, scaled timeline, course suggestions, skill-gap hints, short explanation text
- Persists each generation to MongoDB (`history` and `learning_paths`)
- `GET /history` — list past generations for the logged-in user
- **OpenAI** expands the ML roadmap into structured day-wise plans, explanations, and tips (`OPENAI_API_KEY`)
- **YouTube Data API** attaches 2–3 videos per phase (`YOUTUBE_API_KEY`)
- **Adaptive learning**: step feedback in MongoDB extends difficult phases on the next run
- Curated **`ml_model/data/courses.json`** mapped to phase topics
- Response cache for identical `/generate-path` requests (TTL configurable)
- Optional **TensorFlow** script under `ml_model/optional_nn_tensorflow.py` (install TensorFlow separately)

## Prerequisites

- **Node.js 18+** and npm
- **Python 3.9+** (3.10+ recommended)
- **MongoDB** running locally or a connection URI (e.g. MongoDB Atlas)

## Project layout

| Path        | Description |
|------------|-------------|
| `client/`  | React + Vite + Tailwind SPA |
| `server/`  | FastAPI app (`main.py`), JWT auth, API routes |
| `ml_model/` | TF–IDF recommender, level classifier, sample CSV/JSON data |
| `database/` | MongoDB connection helpers and schema notes |
| `docs/`    | API documentation and example requests |

## Quick start

### 1. MongoDB

Start MongoDB (example):

```bash
# macOS (Homebrew)
brew services start mongodb-community@7.0
```

Or set `MONGODB_URI` to your Atlas cluster in `server/.env`.

### 2. Backend

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env — set JWT_SECRET and MONGODB_URI if needed
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend

```bash
cd client
npm install
cp .env.example .env
# Optional: VITE_API_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Register, then use the dashboard to generate paths.

## Environment variables

**`server/.env`** (see `server/.env.example`):

- `MONGODB_URI` — Mongo connection string
- `MONGODB_DB_NAME` — database name (default `learning_path_app`)
- `JWT_SECRET` — long random string for signing tokens
- `JWT_EXP_HOURS` — token lifetime
- `CORS_ORIGINS` — comma-separated allowed origins for the SPA
- `OPENAI_API_KEY` / `OPENAI_MODEL` — LLM enrichment (optional; fallback template if empty)
- `YOUTUBE_API_KEY` — video search (optional; empty list if missing)
- `GENERATE_CACHE_TTL_SECONDS` — cache lifetime for `/generate-path`
- `YOUTUBE_MAX_PER_TOPIC` — max videos per phase

### OpenAI and YouTube API keys

The backend loads **`server/.env`** with **python-dotenv** as soon as `server/config.py` is imported. API keys are read with **`os.getenv("OPENAI_API_KEY", "")`** and **`os.getenv("YOUTUBE_API_KEY", "")`** (empty string if unset).

1. Copy the example file: `cp server/.env.example server/.env`
2. Edit **`server/.env`** and add (no quotes required unless the value has spaces):

   ```env
   OPENAI_API_KEY=sk-...your-key...
   YOUTUBE_API_KEY=AIza...your-key...
   ```

3. Restart **uvicorn** after changing `.env`.

**Behavior if a key is missing**

- **`OPENAI_API_KEY`** empty → the API still works; the **OpenAI service** returns the **local fallback roadmap** (structured template from ML phases). The server logs a **WARNING** once when settings are first loaded.
- **`YOUTUBE_API_KEY`** empty → **YouTube** returns an **empty video list** for each phase (no HTTP call). A **WARNING** is logged once at settings load.

**Security**

- **Never commit** `server/.env` or paste real keys into README, source code, or chat. Add `server/.env` to `.gitignore` (already in this project). If a key is exposed, **revoke it** in the [OpenAI](https://platform.openai.com/api-keys) and [Google Cloud](https://console.cloud.google.com/apis/credentials) consoles and create a new one.

**YouTube:** enable **YouTube Data API v3** on a Google Cloud project and create an API key with that API enabled.

**`client/.env`** (see `client/.env.example`):

- `VITE_API_URL` — backend base URL (default `http://localhost:8000`)

## Machine learning

- **Dataset**: `ml_model/data/learning_paths.csv` and `ml_model/data/phases_by_role.json`
- **Recommender**: `TfidfVectorizer` on role + skills + summary text; **cosine similarity** to pick the best catalog row; phases are scaled by hours/day and experience level
- **Level classifier**: `ExperienceLevelClassifier` trains small models on first run and saves them under `ml_model/saved_models/` (gitignored)
- **Optional TensorFlow**: `ml_model/optional_nn_tensorflow.py` — `pip install tensorflow` to experiment

## API overview

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | No | Create user, returns JWT |
| POST | `/login` | No | Login, returns JWT |
| POST | `/generate-path` | Bearer JWT | ML + LLM + YouTube + courses + gaps (cached) |
| POST | `/feedback` | Bearer JWT | Step completed / not understood |
| GET | `/feedback` | Bearer JWT | List your feedback |
| DELETE | `/feedback/{id}` | Bearer JWT | Remove a feedback row |
| GET | `/history` | Bearer JWT | List recent generations |
| GET | `/health` | No | Health check |

See `docs/API.md` for request/response examples.

## Production notes

- Replace default `JWT_SECRET` and restrict `CORS_ORIGINS`
- Run behind HTTPS and a reverse proxy (nginx, Caddy, etc.)
- Use a managed MongoDB tier for durability
- Consider rate limiting and request logging on `/register` and `/generate-path`

## License

MIT (or your choice — update as needed).
