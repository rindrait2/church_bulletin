import asyncio
import os
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from auth import get_password_hash

# Use SQLite in-memory for tests with shared cache so all connections see same DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///file:test?mode=memory&cache=shared&uri=true"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Import all models so metadata is populated
import models  # noqa: F401


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client():
    from main import app
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def seed_users(db_session: AsyncSession):
    from models.user import User
    admin = User(username="admin", hashed_password=get_password_hash("admin123"), role="admin")
    editor = User(username="editor", hashed_password=get_password_hash("editor123"), role="editor")
    db_session.add(admin)
    db_session.add(editor)
    await db_session.commit()


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, seed_users):
    response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def editor_token(client: AsyncClient, seed_users):
    response = await client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def seed_bulletin(db_session: AsyncSession):
    from models.bulletin import Bulletin
    from models.program import ProgramItem
    from models.coordinator import Coordinator
    from models.announcement import Announcement

    bulletin = Bulletin(
        id="2026-01-24", date="January 24, 2026", lesson_code="Q1 L4",
        lesson_title="Unity Through Humility", sabbath_ends="6:06 PM", next_sabbath="6:09 PM",
    )
    db_session.add(bulletin)
    await db_session.flush()

    db_session.add_all([
        ProgramItem(bulletin_id="2026-01-24", block="lesson_study", sequence=1, role="Lesson Study",
                    note="Q1 L4 – Unity Through Humility", person="SS Classes"),
        ProgramItem(bulletin_id="2026-01-24", block="ss_program", sequence=1, role="Praise & Worship", person="GraceForce"),
        ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=1, role="Welcome", person="Victor Montano"),
        ProgramItem(bulletin_id="2026-01-24", block="divine_service", sequence=2, role="Message",
                    note="In or Out", person="Dan Smith", is_sermon=True),
    ])

    db_session.add_all([
        Coordinator(bulletin_id="2026-01-24", type="worship", value="Combined Worship at the Church"),
        Coordinator(bulletin_id="2026-01-24", type="deacons", value="Anthoney Thangiah & deacons"),
        Coordinator(bulletin_id="2026-01-24", type="greeters", value="Wan & Group (China)"),
    ])

    db_session.add_all([
        Announcement(bulletin_id="2026-01-24", sequence=1, title="Fellowship Lunch",
                     body="Visitors invited to University Cafeteria.", recurring=True),
        Announcement(bulletin_id="2026-01-24", sequence=2, title="Cushion for Church",
                     body="Donate a cushion."),
    ])

    await db_session.commit()
    return bulletin
