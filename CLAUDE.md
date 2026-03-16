# CLAUDE.md — AIU Church Bulletin API

## Project overview

Build a production-ready REST API for the Asia-Pacific International University (AIU) Church bulletin management system. The API powers a Flutter mobile app used by church staff and students.

---

## Execution rules

- Work autonomously. Do not ask clarifying questions mid-task.
- Complete each phase fully before moving to the next.
- After all phases are done, print a summary of what was built, any assumptions made, and how to run the project.
- If a decision must be made that is not covered here, choose the simpler option and note it in the summary.

---

## Tech stack

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| Language | Python 3.11+ |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL |
| Migrations | Alembic |
| Auth | JWT (python-jose + passlib) |
| Validation | Pydantic v2 |
| Server | Uvicorn |
| Testing | Pytest + httpx |
| Env config | python-dotenv |

---

## Project structure

Create exactly this layout:

```
church_bulletin_api/
├── CLAUDE.md
├── .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
├── alembic/
│   └── versions/
├── main.py
├── database.py
├── auth.py
├── dependencies.py
├── models/
│   ├── __init__.py
│   ├── bulletin.py
│   ├── program.py
│   ├── coordinator.py
│   ├── announcement.py
│   ├── calendar_event.py
│   ├── member.py
│   ├── team.py
│   ├── group.py
│   └── contact.py
├── schemas/
│   ├── __init__.py
│   ├── bulletin.py
│   ├── program.py
│   ├── coordinator.py
│   ├── announcement.py
│   ├── calendar_event.py
│   ├── member.py
│   ├── team.py
│   ├── group.py
│   ├── contact.py
│   └── common.py
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── bulletins.py
│   ├── programs.py
│   ├── coordinators.py
│   ├── announcements.py
│   ├── calendar.py
│   ├── members.py
│   ├── teams.py
│   ├── groups.py
│   ├── contacts.py
│   └── search.py
├── seed.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_bulletins.py
    ├── test_programs.py
    ├── test_announcements.py
    └── test_auth.py
```

---

## Environment variables

Create `.env.example` with these keys:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/church_bulletin
SECRET_KEY=your-secret-key-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## Database models

### `bulletins`
```
id              VARCHAR(20) PRIMARY KEY        e.g. "2026-01-24"
date            VARCHAR(50) NOT NULL           e.g. "January 24, 2026"
lesson_code     VARCHAR(20)                    e.g. "Q1 L4"
lesson_title    VARCHAR(200)
sabbath_ends    VARCHAR(20)                    e.g. "6:06 PM"
next_sabbath    VARCHAR(20)
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
```

### `program_items`
```
id              SERIAL PRIMARY KEY
bulletin_id     VARCHAR(20) FK bulletins(id) CASCADE DELETE
block           VARCHAR(30)     "lesson_study" | "ss_program" | "divine_service"
sequence        INTEGER NOT NULL
role            VARCHAR(100)    e.g. "Welcome", "Pastoral Prayer"
note            VARCHAR(200)    e.g. song title, scripture reference
person          VARCHAR(200)    free text, denormalized
is_sermon       BOOLEAN DEFAULT FALSE
```

### `coordinators`
```
id              SERIAL PRIMARY KEY
bulletin_id     VARCHAR(20) FK bulletins(id) CASCADE DELETE
type            VARCHAR(30)     "worship" | "deacons" | "greeters"
value           TEXT
```

### `announcements`
```
id              SERIAL PRIMARY KEY
bulletin_id     VARCHAR(20) FK bulletins(id) CASCADE DELETE
sequence        INTEGER NOT NULL
title           VARCHAR(200)
body            TEXT
recurring       BOOLEAN DEFAULT FALSE
pinned          BOOLEAN DEFAULT FALSE
```

### `calendar_events`
```
id              SERIAL PRIMARY KEY
day             VARCHAR(20)     "Monday-Friday" | "Wednesday" | "Saturday"
time            VARCHAR(20)     e.g. "7:00 AM"
name            VARCHAR(100)    e.g. "Morning Manna"
location        VARCHAR(100)    e.g. "SB102"
active          BOOLEAN DEFAULT TRUE
```

### `members`
```
id              SERIAL PRIMARY KEY
name            VARCHAR(100) NOT NULL
email           VARCHAR(100)
phone           VARCHAR(30)
active          BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP DEFAULT NOW()
```

### `member_roles`
```
id              SERIAL PRIMARY KEY
member_id       INTEGER FK members(id) CASCADE DELETE
role            VARCHAR(50)    "deacon" | "greeter" | "worship_leader" | "elder" | "pathfinder_leader" | "ay_leader"
```

### `teams`
```
id              SERIAL PRIMARY KEY
name            VARCHAR(100) NOT NULL
type            VARCHAR(50)    "worship_team" | "choir"
active          BOOLEAN DEFAULT TRUE
```

### `groups`
```
id              SERIAL PRIMARY KEY
name            VARCHAR(100) NOT NULL
type            VARCHAR(50)    "nationality" | "ministry"
active          BOOLEAN DEFAULT TRUE
```

### `contacts`
```
id              SERIAL PRIMARY KEY
name            VARCHAR(100)
category        VARCHAR(50)    "pastoral_staff" | "membership_transfer" | "flower_donation" | "bulletin"
email           VARCHAR(100)
phone           VARCHAR(30)
display_order   INTEGER DEFAULT 0
```

### `users` (for auth only)
```
id              SERIAL PRIMARY KEY
username        VARCHAR(100) UNIQUE NOT NULL
hashed_password VARCHAR(200) NOT NULL
role            VARCHAR(20)    "viewer" | "editor" | "admin"
active          BOOLEAN DEFAULT TRUE
created_at      TIMESTAMP DEFAULT NOW()
```

---

## API endpoints

### Auth — `/auth`
```
POST   /auth/login              body: {username, password} → {access_token, refresh_token, token_type}
POST   /auth/refresh            body: {refresh_token}      → {access_token}
GET    /auth/me                 header: Bearer token       → current user info
```

### Bulletins — `/bulletins`
```
GET    /bulletins               public    query: ?limit=10&offset=0&order=desc
POST   /bulletins               editor+   body: BulletinCreate
GET    /bulletins/{id}          public    bulletin header only
PUT    /bulletins/{id}          editor+   body: BulletinUpdate
DELETE /bulletins/{id}          admin
GET    /bulletins/{id}/full     public    bulletin + all subcollections in one response
```

### Programs — `/bulletins/{id}/programs`
```
GET    /bulletins/{id}/programs             public    returns items grouped by block
POST   /bulletins/{id}/programs             editor+   body: ProgramItemCreate
PUT    /bulletins/{id}/programs/{item_id}   editor+   body: ProgramItemUpdate
DELETE /bulletins/{id}/programs/{item_id}   editor+
PATCH  /bulletins/{id}/programs/reorder     editor+   body: [{id, sequence}]
```

### Coordinators — `/bulletins/{id}/coordinators`
```
GET    /bulletins/{id}/coordinators             public
PUT    /bulletins/{id}/coordinators/{type}      editor+   body: {value: "..."}
GET    /coordinators?from=2026-01-01&to=2026-03-31   public   range view
```

### Announcements — `/bulletins/{id}/announcements`
```
GET    /bulletins/{id}/announcements            public
POST   /bulletins/{id}/announcements            editor+   body: AnnouncementCreate
PUT    /bulletins/{id}/announcements/{ann_id}   editor+   body: AnnouncementUpdate
DELETE /bulletins/{id}/announcements/{ann_id}   editor+
```

### Calendar — `/calendar`
```
GET    /calendar            public    all active recurring events
POST   /calendar            admin     body: CalendarEventCreate
PUT    /calendar/{id}       admin     body: CalendarEventUpdate
DELETE /calendar/{id}       admin
```

### Members — `/members`
```
GET    /members                 editor+   query: ?role=deacon&active=true&q=name
POST   /members                 editor+   body: MemberCreate
GET    /members/{id}            editor+
PUT    /members/{id}            editor+   body: MemberUpdate
DELETE /members/{id}            admin
GET    /members/{id}/history    editor+   all program_items assigned to this person (by name match)
```

### Teams — `/teams`
```
GET    /teams               public
POST   /teams               editor+
PUT    /teams/{id}          editor+
DELETE /teams/{id}          admin
```

### Groups — `/groups`
```
GET    /groups              public
POST   /groups              editor+
PUT    /groups/{id}         editor+
DELETE /groups/{id}         admin
```

### Contacts — `/contacts`
```
GET    /contacts                        public    query: ?category=pastoral_staff
POST   /contacts                        admin
PUT    /contacts/{id}                   admin
DELETE /contacts/{id}                   admin
```

### Search — `/search`
```
GET    /search?q=&type=&from=&to=       public
```
Search across: program_items (role, note, person), announcements (title, body), coordinators (value), members (name). Return results grouped by type with bulletin date context.

---

## Response envelope

Every response — success or error — must follow this shape:

```python
# Success
{
  "success": True,
  "data": { ... },       # dict, list, or null
  "message": "OK",
  "meta": {              # only on paginated list responses
    "total": 42,
    "limit": 10,
    "offset": 0
  }
}

# Error
{
  "success": False,
  "data": None,
  "message": "Bulletin not found",
  "code": 404
}
```

Create a helper in `schemas/common.py`:

```python
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class Meta(BaseModel):
    total: int
    limit: int
    offset: int

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: str = "OK"
    meta: Optional[Meta] = None
    code: Optional[int] = None
```

Use this wrapper on every router response.

---

## Auth implementation

- JWT-based, stateless
- Roles: `viewer` (read-only public), `editor` (CRUD on content), `admin` (full access including users, contacts, calendar)
- Public endpoints (GET most resources) require no token
- Protected endpoints check `Authorization: Bearer <token>` header
- Role hierarchy: admin > editor > viewer

In `dependencies.py` create:
```python
get_current_user()       # requires valid token
require_editor()         # role must be editor or admin
require_admin()          # role must be admin
```

---

## `GET /bulletins/{id}/full` response shape

This is the most important endpoint — the Flutter app calls this to render a complete bulletin screen.

```json
{
  "success": true,
  "data": {
    "id": "2026-01-24",
    "date": "January 24, 2026",
    "lessonCode": "Q1 L4",
    "lessonTitle": "Unity Through Humility",
    "sabbathEnds": "6:06 PM",
    "nextSabbath": "6:09 PM",
    "program": {
      "lessonStudy": [
        {"id": 1, "sequence": 1, "role": "Lesson Study", "note": "Q1 L4 – Unity Through Humility", "person": "SS Classes", "isSermon": false}
      ],
      "ssProgram": [
        {"id": 2, "sequence": 1, "role": "Praise & Worship", "note": null, "person": "GraceForce", "isSermon": false},
        {"id": 3, "sequence": 2, "role": "Message in Song", "note": null, "person": "GraceForce", "isSermon": false},
        {"id": 4, "sequence": 3, "role": "Message", "note": "What the Angels Said", "person": "Dan Smith", "isSermon": false}
      ],
      "divineService": [
        {"id": 5, "sequence": 1, "role": "Welcome", "note": null, "person": "Victor Montano", "isSermon": false},
        {"id": 13, "sequence": 9, "role": "Message", "note": "In or Out", "person": "Dan Smith", "isSermon": true}
      ]
    },
    "coordinators": {
      "worship": "Combined Worship at the Church",
      "deacons": "Anthoney Thangiah & deacons; Marry Jane Bambury & Mirma Naag",
      "greeters": "Wan & Group (China)"
    },
    "announcements": [
      {"id": 1, "sequence": 1, "title": "Fellowship Lunch", "body": "Visitors are invited...", "recurring": true, "pinned": false}
    ]
  }
}
```

---

## Seed data (`seed.py`)

Populate the database with all 5 existing bulletins from the church bulletins (Jan 24, Jan 31, Feb 14, Feb 28, Mar 7 — all 2026). Include:
- Full program items for all three blocks per bulletin
- All coordinators (this week values only)
- All announcements
- All contacts as listed in the bulletins
- All calendar events (Morning Manna, MIT, Mid-Week Prayer, Sabbath School, Divine Service, Pathfinder, AY)
- Two seed users: `admin / admin123` (role: admin) and `editor / editor123` (role: editor)

Run with: `python seed.py`

---

## Bulletin data reference

### January 24, 2026 — "In or Out" by Dan Smith (Matt 25:10-13)
Lesson: Q1 L4 – Unity Through Humility | Combined Worship at the Church | Sabbath ends 6:06 PM

**Lesson Study block:** Lesson Study (Q1 L4 – Unity Through Humility) → SS Classes

**SS Program block:**
Praise & Worship → GraceForce | Message in Song → GraceForce | Message (What the Angels Said) → Dan Smith | Translator → Surachet Insom

**Divine Service block:**
Welcome → Victor Montano | Welcome Song (Welcome to the Family) → GraceForce | Praise & Worship → GraceForce | Introit (Be Still, For the Presence of the Lord) → GraceForce | Invocation → Dan Smith | Hymn of Praise (Worthy is the Lamb) → GraceForce | Pastoral Prayer → Victor Montano | Call for Offering → Haydn Golden | Offertory → Sergio Leiva | Message in Song → AIU Choir | Scripture Reading (Matthew 25:10-13) → Athitiya Kattiya | **Message [SERMON]: "In or Out" → Dan Smith** | Closing Song (Assurance Song) → GraceForce | Benediction → Dan Smith | Translator → Nakhon Kitjaroonchai, Kamolnan Taweeyanyongkul | Pianist → Sergio Leiva

**Coordinators:** worship=Combined Worship at the Church | deacons=Anthoney Thangiah & deacons; Marry Jane Bambury & Mirma Naag | greeters=Wan & Group (China)

**Announcements:**
1. Fellowship Lunch — Visitors invited to University Cafeteria. Coupons from Mrs. Ritha Maidom at reception desk.
2. Cushion for Church — Donate a cushion: 1.9m=1200 baht, 1.4m=800 baht. Krungsri Bank acct 055-1-84654-2. Mark: Cushion for Church.
3. AIU English Bible Camp 2026 — Feb 20-22 at Mela Garden Cottage. Theme: Chosen, Called, Committed. Speaker: Pr. Kenneth Martinez. Fee: 800 baht.
4. Flower Donation — From Arts and Humanities (English Thai Program) for thanksgiving.

---

### January 31, 2026 — "What Happened to Harry Orchard?" by George Knight (John 3:5)
Lesson: Q1 L5 – Shining as Lights in the Night | English Service at the Auditorium | Sabbath ends 6:13 PM

**Lesson Study block:** Lesson Study (Q1 L5 – Shining as Lights in the Night) → SS Classes

**SS Program block:**
Praise & Worship → Jubiana Jikson & Co. | Mission Spotlight → Gerald Mahedhie | Mission 360° → Video

**Divine Service block:**
Welcome → Noah Balraj | Welcome Song (Welcome to the Family) → Jubiana Jikson & Co. | Praise & Worship → Jubiana Jikson & Co. | Introit (Be Still, For the Presence of the Lord) → Jubiana Jikson & Co. | Sabbath Song of Celebration (It's the Sabbath) → Jubiana Jikson & Co. | Invocation → George Knight | Hymn of Praise (SDAH#250 O for a Thousand Tongues to Sing) → Jubiana Jikson & Co. | Pastoral Prayer → Noah Balraj | Call for Offering (Church Combined Budget) → Hamengamon Kharsynniang | Offertory → Pianist | Children's Story → Yadahron Hexo | Message in Song → Geya and Mario | Scripture Reading (John 3:5) → Josephine Nakalita | **Message [SERMON]: "What Happened to Harry Orchard?" → George Knight** | Closing Song (SDAH#109 Marvelous Grace) → Jubiana Jikson & Co. | Benediction → George Knight | Pianist → Evelyn Salibio

**Coordinators:** worship=English Service at the Auditorium | deacons=Kameta Katenga; Selfa Montano & Rojean Marcia | greeters=Myanmar Group

**Announcements:**
1. Fellowship Lunch — AIU Church Dining Hall immediately after Divine Service.
2. Cushion for Church — Same as Jan 24.
3. AIU English Bible Camp 2026 — Same as Jan 24.

---

### February 14, 2026 — "The Final Argument" by Loren Agrey (1 John 4:7-12)
Lesson: Q1 L7 – A Heavenly Citizenship | English Service at the Auditorium | Sabbath ends 6:18 PM

**Lesson Study block:** Lesson Study (Q1 L7 – A Heavenly Citizenship) → SS Classes

**SS Program block:**
Praise & Worship → Praise Him | Opening Remarks → Mallen Cortes | Opening Prayer → Sreyna Pok | Mission Spotlight → Charleen Niebres | Mission 360° → Video | Closing Prayer → Charleen Niebres

**Divine Service block:**
Welcome → Franklin Hutabarat | Welcome Song (Welcome to the Family) → Praise Him | Praise & Worship → Praise Him | Introit (Be Still, For the Presence of the Lord) → Praise Him | Sabbath Song of Celebration (It's the Sabbath) → Praise Him | Invocation → Loren Agrey | Hymn of Praise (SDAH#171 Thine is the Glory) → Praise Him | Pastoral Prayer → Franklin Hutabarat | Call for Offering (Church Combined Budget) → Hiram Reagan Panggabean | Offertory → Zamira & Nisa | Children's Story → Brian Sam Agum | Message in Song → Praise Him | Scripture Reading (1 John 4:7-12) → Rhein Daimoye | **Message [SERMON]: "The Final Argument" → Loren Agrey** | Closing Song (SDAH#183 I Will Sing of Jesus Love) → Praise Him | Benediction → Loren Agrey | Pianist → Adelaide Francis

**Coordinators:** worship=English Service at the Auditorium | deacons=Haydn Golden; Clarie Gura & Nerliza Flores | greeters=Salem & Ethiopian group

**Announcements:**
1. Flower Contribution — From Mr. Victor Win Htet Aung for thanksgiving for Thai and International Church.
2. Fellowship Lunch — Ground Floor of the IT Building (near First Aid Clinic) after Divine Service.
3. Fasting & Prayer Sabbath Feb 21 — Fri Feb 20: 6-7pm Fellowship Hall. Sat Feb 21: 8-9am and 2-5pm Fellowship Hall/Mother's Room.
4. Health Ministry — Outreach group meets at 1:30 PM in SB201.
5. Dorcas Ministry — Free lunchboxes Feb 15, 11AM-12:30PM, in front of cafeteria, first come first served.
6. Combined Church Service Feb 21 — Guest speaker: Dr. Ginger Ketting-Weller, President of AIIAS.

---

### February 28, 2026 — "Praise the Lord; the Tractor's Broken" by Ginger Ketting-Weller (Psalm 56:8-11)
Lesson: Q1 L9 – Reconciliation and Hope | Combined Service at the Church | Sabbath ends 6:22 PM

**Lesson Study block:** Lesson Study (Q1 L9 – Reconciliation and Hope) → SS Classes

**SS Program block:**
Praise & Worship → AIU Chorale | Presentation (Grounded in the Bible. Focused on the Mission through Literature Ministry) → Rey Cabanero

**Divine Service block:**
Welcome → Gerard Bernard | Welcome Song (Welcome to the Family) → AIU Chorale | Praise & Worship → AIU Chorale | Introit (Be Still, For the Presence of the Lord) → AIU Chorale | Sabbath Song of Celebration (It's the Sabbath) → AIU Chorale | Invocation → Ginger Ketting-Weller | Hymn of Praise (SDAH#528 A Shelter in the Time of Storm) → AIU Chorale | Pastoral Prayer → Gerard Bernard | Call for Offering (Church Combined Budget) → Kameta Katenga | Offertory → AIMS Connection | Children's Story → Judith Joel (Translator: Peeranat Kongsang) | Message in Song → AIU Chorale | Scripture Reading (Psalm 56:8-11) → Leonarde Valwen Tan | **Message [SERMON]: "Praise the Lord; the Tractor's Broken" → Ginger Ketting-Weller** | Closing Song (SDAH#99 God Will Take Care of You) → AIU Chorale | Benediction → Ginger Ketting-Weller | Pianist → Anna Mathew | Translators → Tantip Kitjaroonchai, Surachet Insom

**Coordinators:** worship=Combined Service at the Church | deacons=Alby Mathew Jacob; Deanna Hutabarat & Lalhmunmawii Kachchhap | greeters=Mili and Indian group

**Announcements:**
1. Fellowship Lunch — AIU Church Dining Hall immediately after Divine Service.
2. Health Ministry — Outreach group meets at 1:30 PM in SB201.
3. Church Services Next Sabbath Mar 7 — International Church: AIU Church. Thai Church: Fellowship Hall.
4. Indoor Games Multi-Generational Mar 3 — Tue March 3, 9AM-5PM, IT Second Floor APIU. Free. Bible games, fellowship, themed meals. Contact: Prema Marshall +66 954 670 461.

---

### March 7, 2026 — "Teachers Wanted" by Victor Bejota (Acts 8:29-31)
Lesson: Q1 L10 – Complete in Christ | English Service at the Church | Sabbath ends 6:24 PM

**Lesson Study block:** Lesson Study (Q1 L10 – Complete in Christ) → SS Classes

**SS Program block:**
Praise & Worship → Addel Joe & Co. | Mission Spotlight → Moite Kachchhap | Mission 360° → Video | Pianist → Adriana Masilung

**Divine Service block:**
Welcome → Alfredo Agustin | Welcome Song (Welcome to the Family) → Addel Joe & Co. | Praise & Worship → Addel Joe & Co. | Introit (Be Still, For the Presence of the Lord) → Addel Joe & Co. | Sabbath Song of Celebration (It's the Sabbath) → Addel Joe & Co. | Invocation → Victor Bejota | Hymn of Praise (SDAH#272 Give Me the Bible) → Addel Joe & Co. | Pastoral Prayer → Alfredo Agustin | Call for Offering (Church Combined Budget) → Anthoney Thangiah | Offertory → Masilung Sisters | Children's Story → Yarmichon Zimik | Message in Song → Voice of Harmony | Scripture Reading (Acts 8:29-31) → Selected | **Message [SERMON]: "Teachers Wanted" → Victor Bejota** | Closing Song (SDAH#340 Jesus Saves) → Addel Joe & Co. | Benediction → Victor Bejota | Pianist → Adriana Masilung

**Coordinators:** worship=English Service at the Church | deacons=Honesto Encapas; Alvina Sulankey & Yarmichon Zimik | greeters=Melody and Indonesian group

**Announcements:**
1. Flower Contribution — From Mr. Victor Win Htet Aung for thanksgiving for Thai and International Church.
2. Note of Appreciation — Gratitude to Korean donors for two brand-new projectors now installed and operational.
3. Fellowship Lunch — University Cafeteria. Coupons from Mrs. Ritha Maidom at reception desk.
4. Health Ministry — Outreach group meets at 1:30 PM in SB201.

---

## Contacts data

```
Pastoral Staff:
  Dr. Surachet Insom | surachet@apiu.edu | 0898932770
  Pr. Victor Bejota  | int.pastor@apiu.edu | 0812604200
  Pr. Dal Za Kap     | dalzakap@apiu.edu | 0634193342

Membership Transfer:
  Khun Thitaree Sirikulpat | thitaree@seumsda.org

Flower Donation:
  Ms. Payom Sriharat | mc-mart@apiu.edu | 0836933916

Church Bulletin:
  Ms. Chrystal Naltan | chrystal@apiu.edu | 0944130176
```

---

## Calendar events data

```
day=Monday-Friday | time=7:00 AM  | name=Morning Manna     | location=SB102
day=Wednesday     | time=5:00 PM  | name=MIT               | location=
day=Wednesday     | time=7:00 PM  | name=Mid-Week Prayer   | location=
day=Saturday      | time=9:00 AM  | name=Sabbath School    | location=
day=Saturday      | time=10:30 AM | name=Divine Service    | location=
day=Saturday      | time=3:00 PM  | name=Pathfinder        | location=
day=Saturday      | time=5:00 PM  | name=AY                | location=
```

---

## Requirements file

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

---

## main.py requirements

- Include all routers with prefix `/api/v1`
- Enable CORS for all origins (students will call from emulators and physical devices)
- Mount Swagger UI at `/docs` and ReDoc at `/redoc`
- Add startup event that logs confirmation of DB connection
- Global exception handler that returns the error envelope format

---

## Code quality rules

- All routes must be async
- All DB operations use async SQLAlchemy sessions
- No raw SQL — use ORM only
- Every router function has a docstring
- Use dependency injection for DB session and auth
- HTTP status codes must be correct: 200 GET, 201 POST, 200 PUT, 204 DELETE, 404 not found, 401 unauthorized, 403 forbidden, 422 validation error
- Validation errors from Pydantic must also be wrapped in the response envelope

---

## Tests

Write tests in `tests/` covering:
- `test_auth.py` — login success, login fail, token refresh, protected route without token
- `test_bulletins.py` — list, get by id, get full, create (auth), update (auth), 404 case
- `test_programs.py` — list grouped by block, create, reorder
- `test_announcements.py` — list, create, update, delete

Use an in-memory SQLite database for tests (override DATABASE_URL in conftest.py).

---

## How to run

After generating all files, print these instructions:

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill env file
cp .env.example .env

# 4. Run migrations
alembic upgrade head

# 5. Seed the database
python seed.py

# 6. Start the server
uvicorn main:app --reload --port 8000

# 7. Open API docs
http://localhost:8000/docs
```
