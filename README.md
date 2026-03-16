# AIU Church Bulletin API

REST API for the Asia-Pacific International University (AIU) Church bulletin management system, built with FastAPI and PostgreSQL.

---

## Prerequisites

- **Python 3.11+** — [Download](https://www.python.org/downloads/)
- **PostgreSQL** — via Docker (recommended) or a cloud provider
- **Git**
- **Docker** (optional) — for the easiest one-command setup

---

## Quick Start (Docker — easiest)

```bash
git clone <repo-url>
cd church_bulletin
docker compose up -d --build
```

This starts both PostgreSQL and the API. Then seed the database:

```bash
docker compose exec api python seed.py
```

The API is now running at **http://localhost:8000**. Skip to the [API Documentation](#api-documentation) section.

---

## Quick Start (Manual)

### 1. Clone the repository

```bash
git clone <repo-url>
cd church_bulletin
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up the database

**Option A — Docker (recommended)**

```bash
docker run -d --name church_db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=church_bulletin \
  -p 5432:5432 \
  postgres:16
```

**Option B — Cloud database**

Use a free PostgreSQL provider like [Supabase](https://supabase.com), [Neon](https://neon.tech), or [Railway](https://railway.app). Copy the connection string they provide.

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your database credentials:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/church_bulletin
SECRET_KEY=change-this-to-a-random-string-at-least-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

> If using a cloud database, replace the `DATABASE_URL` with your provider's connection string. Make sure it starts with `postgresql+asyncpg://`.

### 6. Seed the database

This creates all tables and populates them with sample data (5 church bulletins, contacts, calendar events, and test users).

```bash
python seed.py
```

### 7. Start the server

```bash
uvicorn main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**.

---

## API Documentation

Once the server is running, open your browser:

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI — interactive API explorer |
| http://localhost:8000/redoc | ReDoc — readable API reference |

You can test every endpoint directly from the Swagger UI.

---

## Authentication

The API uses JWT tokens. Some endpoints are public (no token needed), while others require authentication.

### Test accounts

| Username | Password | Role | Access |
|---|---|---|---|
| `admin` | `admin123` | Admin | Full access (all CRUD, users, contacts, calendar) |
| `editor` | `editor123` | Editor | Create/update content (bulletins, programs, announcements) |

### How to authenticate

1. **Get a token** — Send a POST request to `/api/v1/auth/login`:

```json
POST http://localhost:8000/api/v1/auth/login
Content-Type: application/json

{
  "username": "editor",
  "password": "editor123"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
}
```

2. **Use the token** — Add it to the `Authorization` header on protected requests:

```
Authorization: Bearer eyJhbGciOi...
```

3. **In Swagger UI** — Click the **Authorize** button (top right), enter `Bearer <your_token>`, and all subsequent requests will include it automatically.

---

## API Endpoints Overview

All endpoints are prefixed with `/api/v1`.

### Public endpoints (no token required)

| Method | Endpoint | Description |
|---|---|---|
| GET | `/bulletins` | List all bulletins (paginated) |
| GET | `/bulletins/{id}` | Get a single bulletin header |
| GET | `/bulletins/{id}/full` | Get a complete bulletin with programs, coordinators, and announcements |
| GET | `/bulletins/{id}/programs` | List program items grouped by block |
| GET | `/bulletins/{id}/coordinators` | List coordinators for a bulletin |
| GET | `/bulletins/{id}/announcements` | List announcements for a bulletin |
| GET | `/calendar` | List all recurring calendar events |
| GET | `/teams` | List all teams |
| GET | `/groups` | List all groups |
| GET | `/contacts` | List all contacts |
| GET | `/search?q=keyword` | Search across bulletins, announcements, and members |

### Editor endpoints (editor or admin token required)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/bulletins` | Create a new bulletin |
| PUT | `/bulletins/{id}` | Update a bulletin |
| POST | `/bulletins/{id}/programs` | Add a program item |
| PUT | `/bulletins/{id}/programs/{item_id}` | Update a program item |
| DELETE | `/bulletins/{id}/programs/{item_id}` | Delete a program item |
| PATCH | `/bulletins/{id}/programs/reorder` | Reorder program items |
| POST | `/bulletins/{id}/announcements` | Add an announcement |
| PUT | `/bulletins/{id}/announcements/{id}` | Update an announcement |
| DELETE | `/bulletins/{id}/announcements/{id}` | Delete an announcement |
| GET/POST/PUT | `/members` | Manage members |

### Authenticated endpoints (any logged-in user)

| Method | Endpoint | Description |
|---|---|---|
| PUT | `/auth/password` | Change your own password |

### Admin endpoints (admin token required)

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| GET | `/auth/users` | List all users |
| PUT | `/auth/users/{id}` | Update a user's role or active status |
| DELETE | `/bulletins/{id}` | Delete a bulletin |
| POST/PUT/DELETE | `/calendar/{id}` | Manage calendar events |
| POST/PUT/DELETE | `/contacts/{id}` | Manage contacts |
| DELETE | `/members/{id}` | Delete a member |

---

## Connecting from Flutter

Use the base URL `http://<your-computer-ip>:8000/api/v1` in your Flutter app.

**For Android emulator:** use `http://10.0.2.2:8000/api/v1`
**For iOS simulator:** use `http://localhost:8000/api/v1`
**For physical device:** use your computer's local IP (e.g., `http://192.168.x.x:8000/api/v1`)

Example using Dart's `http` package:

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

const baseUrl = 'http://10.0.2.2:8000/api/v1';

// Fetch the full bulletin
final response = await http.get(Uri.parse('$baseUrl/bulletins/2026-01-24/full'));
final data = jsonDecode(response.body);
print(data['data']['program']['divineService']);

// Login
final loginResponse = await http.post(
  Uri.parse('$baseUrl/auth/login'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode({'username': 'editor', 'password': 'editor123'}),
);
final token = jsonDecode(loginResponse.body)['data']['access_token'];

// Create an announcement (authenticated)
final createResponse = await http.post(
  Uri.parse('$baseUrl/bulletins/2026-01-24/announcements'),
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer $token',
  },
  body: jsonEncode({
    'sequence': 5,
    'title': 'New Event',
    'body': 'Details about the event...',
  }),
);
```

---

## Response Format

Every API response follows this structure:

```json
{
  "success": true,
  "data": { ... },
  "message": "OK",
  "meta": {
    "total": 5,
    "limit": 10,
    "offset": 0
  }
}
```

Error responses:

```json
{
  "success": false,
  "data": null,
  "message": "Bulletin not found",
  "code": 404
}
```

---

## Sample Bulletin IDs

The seeded database contains these bulletins:

| ID | Date | Sermon | Speaker |
|---|---|---|---|
| `2026-01-24` | January 24, 2026 | "In or Out" | Dan Smith |
| `2026-01-31` | January 31, 2026 | "What Happened to Harry Orchard?" | George Knight |
| `2026-02-14` | February 14, 2026 | "The Final Argument" | Loren Agrey |
| `2026-02-28` | February 28, 2026 | "Praise the Lord; the Tractor's Broken" | Ginger Ketting-Weller |
| `2026-03-07` | March 7, 2026 | "Teachers Wanted" | Victor Bejota |

---

## Running Tests

```bash
pip install aiosqlite     # needed for SQLite test database
python -m pytest tests/ -v
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Make sure your virtual environment is activated: `source venv/bin/activate` |
| Database connection refused | Check that PostgreSQL is running and your `DATABASE_URL` in `.env` is correct |
| `asyncpg` connection error | Ensure the URL starts with `postgresql+asyncpg://` |
| CORS error in Flutter | The API allows all origins — check that you're using the correct IP address |
| Token expired | Call `/api/v1/auth/refresh` with your refresh token, or log in again |

---

## Tech Stack

- **FastAPI** — async Python web framework
- **SQLAlchemy 2.0** — async ORM
- **PostgreSQL** — database
- **Pydantic v2** — data validation
- **JWT** — authentication (python-jose + passlib)
- **Alembic** — database migrations
