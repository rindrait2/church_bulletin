import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_bulletins(client: AsyncClient, seed_bulletin):
    """Test listing bulletins returns paginated results."""
    response = await client.get("/api/v1/bulletins")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_bulletin_by_id(client: AsyncClient, seed_bulletin):
    """Test getting a bulletin by ID."""
    response = await client.get("/api/v1/bulletins/2026-01-24")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "2026-01-24"


@pytest.mark.asyncio
async def test_get_bulletin_full(client: AsyncClient, seed_bulletin):
    """Test getting a full bulletin with all subcollections."""
    response = await client.get("/api/v1/bulletins/2026-01-24/full")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    bulletin = data["data"]
    assert bulletin["id"] == "2026-01-24"
    assert "lessonStudy" in bulletin["program"]
    assert "ssProgram" in bulletin["program"]
    assert "divineService" in bulletin["program"]
    assert len(bulletin["program"]["lessonStudy"]) >= 1
    assert "worship" in bulletin["coordinators"]
    assert len(bulletin["announcements"]) >= 1


@pytest.mark.asyncio
async def test_create_bulletin_requires_auth(client: AsyncClient):
    """Test creating a bulletin without auth returns 401."""
    response = await client.post("/api/v1/bulletins", json={
        "id": "2026-04-01", "date": "April 1, 2026",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_bulletin(client: AsyncClient, editor_token):
    """Test creating a bulletin with editor auth."""
    response = await client.post(
        "/api/v1/bulletins",
        json={"id": "2026-04-01", "date": "April 1, 2026", "lesson_code": "Q2 L1"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == "2026-04-01"


@pytest.mark.asyncio
async def test_update_bulletin(client: AsyncClient, seed_bulletin, editor_token):
    """Test updating a bulletin."""
    response = await client.put(
        "/api/v1/bulletins/2026-01-24",
        json={"lesson_title": "Updated Title"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["lessonTitle"] == "Updated Title"


@pytest.mark.asyncio
async def test_get_bulletin_404(client: AsyncClient):
    """Test getting a non-existent bulletin returns 404."""
    response = await client.get("/api/v1/bulletins/9999-99-99")
    assert response.status_code == 404
