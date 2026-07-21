# MongoDB schema

## Database name

Default: `learning_path_app` (override with `MONGODB_DB_NAME`).

## Collection: `users`

| Field        | Type     | Description |
|-------------|----------|-------------|
| `_id`       | ObjectId | Primary key |
| `email`     | string   | Unique, lowercase |
| `full_name` | string   | Display name |
| `hashed_password` | string | bcrypt hash |
| `created_at`| datetime | UTC |

## Collection: `learning_paths`

| Field          | Type     | Description |
|----------------|----------|-------------|
| `_id`          | ObjectId | Primary key |
| `user_id`      | string   | User ObjectId as hex string |
| `input`        | object   | skills, goal, experience_level, hours_per_day |
| `generated_output` | object | ML output (roadmap, timeline, etc.) |
| `created_at`   | datetime | UTC |

## Collection: `history`

| Field          | Type     | Description |
|----------------|----------|-------------|
| `_id`          | ObjectId | Primary key |
| `user_id`      | string   | User ObjectId as hex string |
| `input`        | object   | Same as generate-path request |
| `generated_output` | object | Same structure as API response body |
| `created_at`   | datetime | UTC |

Each successful `/generate-path` call appends one document to `history` and one to `learning_paths` with the same payload shape.

## Collection: `step_feedback`

| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Primary key |
| `user_id` | string | Owner |
| `step_index` | int | Index into `base_path.phases` |
| `phase_name` | string | Phase title (for matching) |
| `status` | string | `completed` or `not_understood` |
| `generation_id` | string \| null | Optional `history` document id |
| `created_at` | datetime | UTC |

Used for adaptive extensions on the next `/generate-path` and for UI progress.
