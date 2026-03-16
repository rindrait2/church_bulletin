# API Guide — Hands-On Tutorial

This guide walks you through the AIU Church Bulletin API step by step. Open **http://localhost:8001/docs** (Swagger UI) alongside this guide to try each request interactively.

You can also use tools like **Postman**, **Thunder Client** (VS Code extension), or **curl** from the terminal.

Base URL: `http://localhost:8001/api/v1`

---

## Part 1: Exploring Public Endpoints (No Login Required)

These endpoints are open to everyone — no token needed.

### 1.1 List all bulletins

```
GET /api/v1/bulletins
```

Try adding query parameters:
- `?limit=2` — only return 2 bulletins
- `?offset=2` — skip the first 2
- `?order=asc` — oldest first

**Exercise:** Fetch only the 3 most recent bulletins.

<details>
<summary>Answer</summary>

```
GET /api/v1/bulletins?limit=3&order=desc
```
</details>

---

### 1.2 Get a single bulletin

```
GET /api/v1/bulletins/2026-01-24
```

This returns only the header (date, lesson, sabbath times). Notice the camelCase field names (`lessonCode`, `sabbathEnds`) — these are formatted for Flutter/Dart conventions.

---

### 1.3 Get a FULL bulletin (most important endpoint)

```
GET /api/v1/bulletins/2026-01-24/full
```

This is what your Flutter app will call to render a complete bulletin screen. Study the response structure:

```
data
├── id, date, lessonCode, lessonTitle, sabbathEnds, nextSabbath
├── program
│   ├── lessonStudy: [...]
│   ├── ssProgram: [...]
│   └── divineService: [...]
├── coordinators: { worship, deacons, greeters }
└── announcements: [...]
```

**Exercise:** Find the sermon title and speaker for the January 24 bulletin.

<details>
<summary>Answer</summary>

Look in `data.program.divineService` for the item where `isSermon: true`.
- Title: "In or Out" (in the `note` field)
- Speaker: "Dan Smith" (in the `person` field)
</details>

---

### 1.4 Get programs grouped by block

```
GET /api/v1/bulletins/2026-01-24/programs
```

Returns three groups: `lessonStudy`, `ssProgram`, `divineService`.

---

### 1.5 Get announcements

```
GET /api/v1/bulletins/2026-01-24/announcements
```

---

### 1.6 Get coordinators

```
GET /api/v1/bulletins/2026-01-24/coordinators
```

---

### 1.7 Calendar events

```
GET /api/v1/calendar
```

Returns the weekly recurring events (Morning Manna, Sabbath School, Divine Service, etc.).

---

### 1.8 Contacts

```
GET /api/v1/contacts
```

Filter by category:
```
GET /api/v1/contacts?category=pastoral_staff
```

Valid categories: `pastoral_staff`, `membership_transfer`, `flower_donation`, `bulletin`

---

### 1.9 Search

```
GET /api/v1/search?q=Dan Smith
```

Search across programs, announcements, coordinators, and members. Filter by type:
```
GET /api/v1/search?q=Fellowship&type=announcements
```

**Exercise:** Search for all bulletins where "GraceForce" was involved.

<details>
<summary>Answer</summary>

```
GET /api/v1/search?q=GraceForce&type=programs
```
</details>

---

## Part 2: Authentication

Protected endpoints require a JWT token. Let's get one.

### 2.1 Login

```
POST /api/v1/auth/login
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
    "access_token": "eyJhbG...",
    "refresh_token": "eyJhbG...",
    "token_type": "bearer"
  }
}
```

**Save the `access_token`** — you'll need it for the next steps.

### 2.2 Using the token

Add this header to all protected requests:
```
Authorization: Bearer <your_access_token>
```

**In Swagger UI:** Click the green **Authorize** button at the top, enter `Bearer <your_token>`, click **Authorize**. Now all requests include the token automatically.

### 2.3 Check who you are

```
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### 2.4 Refresh your token

When your access token expires (after 60 minutes), use the refresh token to get a new one without logging in again:

```
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "<your_refresh_token>"
}
```

**Exercise:** Try calling `GET /api/v1/auth/me` without a token. What happens?

<details>
<summary>Answer</summary>

You get a 401 Unauthorized error:
```json
{
  "success": false,
  "data": null,
  "message": "Not authenticated",
  "code": 401
}
```
</details>

---

## Part 3: Creating and Modifying Data (Editor Role)

Login as `editor` / `editor123` for these exercises.

### 3.1 Create a new bulletin

```
POST /api/v1/bulletins
Authorization: Bearer <editor_token>
Content-Type: application/json

{
  "id": "2026-03-14",
  "date": "March 14, 2026",
  "lesson_code": "Q1 L11",
  "lesson_title": "The Whole Armor of God",
  "sabbath_ends": "6:26 PM",
  "next_sabbath": "6:28 PM"
}
```

Expected: `201 Created`

### 3.2 Add program items to your bulletin

```
POST /api/v1/bulletins/2026-03-14/programs
Authorization: Bearer <editor_token>
Content-Type: application/json

{
  "block": "divine_service",
  "sequence": 1,
  "role": "Welcome",
  "person": "Your Name"
}
```

Add a few more items:

```json
{"block": "divine_service", "sequence": 2, "role": "Praise & Worship", "person": "Worship Team"}
{"block": "divine_service", "sequence": 3, "role": "Message", "note": "My Sermon Title", "person": "Speaker Name", "is_sermon": true}
{"block": "lesson_study", "sequence": 1, "role": "Lesson Study", "note": "Q1 L11 – The Whole Armor of God", "person": "SS Classes"}
```

### 3.3 Add announcements

```
POST /api/v1/bulletins/2026-03-14/announcements
Authorization: Bearer <editor_token>
Content-Type: application/json

{
  "sequence": 1,
  "title": "Fellowship Lunch",
  "body": "Everyone is invited to the cafeteria after service.",
  "recurring": true
}
```

### 3.4 Set coordinators

```
PUT /api/v1/bulletins/2026-03-14/coordinators/worship
Authorization: Bearer <editor_token>
Content-Type: application/json

{
  "value": "English Service at the Church"
}
```

Repeat for `deacons` and `greeters`.

### 3.5 View your complete bulletin

```
GET /api/v1/bulletins/2026-03-14/full
```

**Exercise:** Create a complete bulletin for March 14 with at least:
- 3 divine service items (including a sermon)
- 1 lesson study item
- 2 announcements
- All 3 coordinators (worship, deacons, greeters)

Then verify it with the `/full` endpoint.

---

### 3.6 Update a bulletin

```
PUT /api/v1/bulletins/2026-03-14
Authorization: Bearer <editor_token>
Content-Type: application/json

{
  "lesson_title": "Updated Lesson Title"
}
```

Only send the fields you want to change.

### 3.7 Reorder program items

First, get the program items and note their IDs:
```
GET /api/v1/bulletins/2026-03-14/programs
```

Then reorder:
```
PATCH /api/v1/bulletins/2026-03-14/programs/reorder
Authorization: Bearer <editor_token>
Content-Type: application/json

[
  {"id": 100, "sequence": 2},
  {"id": 101, "sequence": 1}
]
```

(Replace 100, 101 with actual IDs from your response.)

### 3.8 Delete an announcement

```
DELETE /api/v1/bulletins/2026-03-14/announcements/{id}
Authorization: Bearer <editor_token>
```

Expected: `204 No Content` (empty response body).

---

## Part 4: Admin Operations

Login as `admin` / `admin123` for these exercises.

### 4.1 Register a new user

```
POST /api/v1/auth/register
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "username": "myname",
  "password": "mypass123",
  "role": "editor"
}
```

Valid roles: `viewer`, `editor`, `admin`

### 4.2 List all users

```
GET /api/v1/auth/users
Authorization: Bearer <admin_token>
```

### 4.3 Change your password

```
PUT /api/v1/auth/password
Authorization: Bearer <any_token>
Content-Type: application/json

{
  "current_password": "admin123",
  "new_password": "mynewpassword"
}
```

### 4.4 Manage calendar events

```
POST /api/v1/calendar
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "day": "Friday",
  "time": "7:00 PM",
  "name": "Vespers",
  "location": "Church"
}
```

### 4.5 Delete a bulletin

```
DELETE /api/v1/bulletins/2026-03-14
Authorization: Bearer <admin_token>
```

This deletes the bulletin AND all its programs, coordinators, and announcements (cascade delete).

---

## Part 5: Understanding the Response Format

Every response follows this structure:

### Success
```json
{
  "success": true,
  "data": { ... },
  "message": "OK",
  "meta": { "total": 5, "limit": 10, "offset": 0 }
}
```

`meta` only appears on paginated list endpoints (like `GET /bulletins`).

### Error
```json
{
  "success": false,
  "data": null,
  "message": "Bulletin not found",
  "code": 404
}
```

### HTTP Status Codes

| Code | Meaning | When |
|---|---|---|
| 200 | OK | Successful GET or PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Token valid but insufficient role |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate (e.g., bulletin ID already exists) |
| 422 | Validation Error | Invalid request body |

---

## Part 6: Flutter Integration Challenge

Build a Flutter screen that:

1. Calls `GET /api/v1/bulletins` to show a list of bulletins
2. When a bulletin is tapped, calls `GET /api/v1/bulletins/{id}/full` to show the full bulletin
3. Displays the program in three sections (Lesson Study, SS Program, Divine Service)
4. Shows the sermon item highlighted (where `isSermon == true`)
5. Shows announcements at the bottom

**Bonus challenges:**
- Add a login screen that calls `POST /api/v1/auth/login` and stores the token
- Let editors add announcements from the app
- Add a search screen using `GET /api/v1/search?q=...`
- Show the weekly calendar from `GET /api/v1/calendar`

---

## Quick Reference: All Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/login` | - | Login |
| POST | `/auth/refresh` | - | Refresh token |
| GET | `/auth/me` | any | Current user info |
| PUT | `/auth/password` | any | Change password |
| POST | `/auth/register` | admin | Register user |
| GET | `/auth/users` | admin | List users |
| PUT | `/auth/users/{id}` | admin | Update user |
| GET | `/bulletins` | - | List bulletins |
| POST | `/bulletins` | editor+ | Create bulletin |
| GET | `/bulletins/{id}` | - | Get bulletin |
| PUT | `/bulletins/{id}` | editor+ | Update bulletin |
| DELETE | `/bulletins/{id}` | admin | Delete bulletin |
| GET | `/bulletins/{id}/full` | - | Full bulletin |
| GET | `/bulletins/{id}/programs` | - | List programs |
| POST | `/bulletins/{id}/programs` | editor+ | Create program |
| PUT | `/bulletins/{id}/programs/{pid}` | editor+ | Update program |
| DELETE | `/bulletins/{id}/programs/{pid}` | editor+ | Delete program |
| PATCH | `/bulletins/{id}/programs/reorder` | editor+ | Reorder programs |
| GET | `/bulletins/{id}/coordinators` | - | List coordinators |
| PUT | `/bulletins/{id}/coordinators/{type}` | editor+ | Set coordinator |
| GET | `/bulletins/{id}/announcements` | - | List announcements |
| POST | `/bulletins/{id}/announcements` | editor+ | Create announcement |
| PUT | `/bulletins/{id}/announcements/{aid}` | editor+ | Update announcement |
| DELETE | `/bulletins/{id}/announcements/{aid}` | editor+ | Delete announcement |
| GET | `/calendar` | - | List events |
| POST | `/calendar` | admin | Create event |
| PUT | `/calendar/{id}` | admin | Update event |
| DELETE | `/calendar/{id}` | admin | Delete event |
| GET | `/members` | editor+ | List members |
| POST | `/members` | editor+ | Create member |
| GET | `/members/{id}` | editor+ | Get member |
| PUT | `/members/{id}` | editor+ | Update member |
| DELETE | `/members/{id}` | admin | Delete member |
| GET | `/members/{id}/history` | editor+ | Member's program history |
| GET | `/teams` | - | List teams |
| POST | `/teams` | editor+ | Create team |
| PUT | `/teams/{id}` | editor+ | Update team |
| DELETE | `/teams/{id}` | admin | Delete team |
| GET | `/groups` | - | List groups |
| POST | `/groups` | editor+ | Create group |
| PUT | `/groups/{id}` | editor+ | Update group |
| DELETE | `/groups/{id}` | admin | Delete group |
| GET | `/contacts` | - | List contacts |
| POST | `/contacts` | admin | Create contact |
| PUT | `/contacts/{id}` | admin | Update contact |
| DELETE | `/contacts/{id}` | admin | Delete contact |
| GET | `/search?q=` | - | Search everything |
