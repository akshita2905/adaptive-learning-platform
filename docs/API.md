# API documentation

Base URL (local): `http://localhost:8000`

All authenticated routes expect:

```http
Authorization: Bearer <access_token>
```

## `POST /register`

Creates a user and returns a JWT (same shape as login).

**Request body (JSON)**

| Field | Type | Notes |
|-------|------|--------|
| `email` | string | Valid email |
| `password` | string | Min 8 characters |
| `full_name` | string | Display name |

**Response `200`**

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "user_id": "<mongo ObjectId hex>",
  "email": "you@example.com",
  "full_name": "Your Name"
}
```

## `POST /login`

**Request body**

| Field | Type |
|-------|------|
| `email` | string |
| `password` | string |

**Response** — same token envelope as `/register`.

## `POST /generate-path`

Requires authentication.

**Request body**

| Field | Type | Notes |
|-------|------|--------|
| `skills` | string[] | Non-empty, e.g. `["Python","SQL"]` |
| `goal` | string | e.g. `"Data Scientist"` |
| `experience_level` | string \| null | `"Beginner"` \| `"Intermediate"` \| `"Advanced"` — omit or send `null` to infer |
| `hours_per_day` | number | `0 < hours ≤ 24` |
| `regenerate_smarter` | boolean | Default `false`. Skips cache and asks the LLM for richer output. |
| `use_cache` | boolean | Default `true`. Return a recent identical payload when available. |

**Response `200`** — nested envelope:

| Field | Description |
|-------|-------------|
| `base_path` | ML layer: `matched_role`, `phases`, `roadmap`, `timeline_*`, `course_suggestions`, `ai_explanation`, `skill_gap_analysis`, `experience_level_used`, optional `predicted_level`, `level_probabilities`, … |
| `ai_roadmap` | LLM JSON: `detailed_plan[]` (per-phase `day_range`, `title`, `tasks`, `explanation`, `learning_tips`), `explanations`, `tips` |
| `videos` | Map `"0"`, `"1"`, … → array of `{ title, thumbnail, url }` (YouTube) |
| `skill_gaps` | `[{ "skill", "priority": "HIGH"\|"MEDIUM"\|"LOW", "score" }]` |
| `courses` | Map topic keyword → curated course title strings (`courses.json`) |
| `generation_id` | Mongo id of this history row (for feedback linkage) |

## `POST /feedback`

Requires authentication. Records step feedback for adaptive roadmaps.

**Body:** `{ "step_index": 0, "phase_name": "Python & SQL", "status": "completed" | "not_understood", "generation_id": "<optional>" }`

## `GET /feedback`

Requires authentication. Recent feedback rows for the user (newest first).

## `DELETE /feedback/{feedback_id}`

Requires authentication. Removes one feedback document you own (e.g. uncheck progress).

## `GET /history`

Requires authentication. Returns up to **50** items, newest first.

Each item:

| Field | Type |
|-------|------|
| `id` | string (Mongo `_id`) |
| `user_id` | string |
| `input` | object (skills, goal, experience_level, hours_per_day) |
| `generated_output` | object (same fields as generate-path response) |
| `created_at` | ISO datetime |

## `GET /health`

Returns `{ "status": "ok" }`.

---

## Example requests (curl)

Replace values as needed.

### Register

```bash
curl -s -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123","full_name":"Demo User"}'
```

### Login

```bash
curl -s -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"password123"}'
```

Save `access_token` from the response as `TOKEN`.

### Generate path

```bash
export TOKEN="<paste_jwt_here>"

curl -s -X POST http://localhost:8000/generate-path \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "skills": ["Python", "SQL"],
    "goal": "Data Scientist",
    "experience_level": "Intermediate",
    "hours_per_day": 2
  }'
```

### Infer experience level (send null)

```bash
curl -s -X POST http://localhost:8000/generate-path \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "skills": ["Python", "pandas", "machine learning"],
    "goal": "ML Engineer",
    "experience_level": null,
    "hours_per_day": 3
  }'
```

### History

```bash
curl -s http://localhost:8000/history \
  -H "Authorization: Bearer $TOKEN"
```

OpenAPI UI: `/docs` (Swagger) and `/redoc`.
