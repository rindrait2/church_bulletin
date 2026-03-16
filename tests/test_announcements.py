import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_announcements(client: AsyncClient, seed_bulletin):
    """Test listing announcements for a bulletin."""
    response = await client.get("/api/v1/bulletins/2026-01-24/announcements")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_create_announcement(client: AsyncClient, seed_bulletin, editor_token):
    """Test creating an announcement."""
    response = await client.post(
        "/api/v1/bulletins/2026-01-24/announcements",
        json={"sequence": 10, "title": "Test Announcement", "body": "Test body"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["title"] == "Test Announcement"


@pytest.mark.asyncio
async def test_update_announcement(client: AsyncClient, seed_bulletin, editor_token):
    """Test updating an announcement."""
    # Get existing announcements
    list_resp = await client.get("/api/v1/bulletins/2026-01-24/announcements")
    ann_id = list_resp.json()["data"][0]["id"]

    response = await client.put(
        f"/api/v1/bulletins/2026-01-24/announcements/{ann_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_announcement(client: AsyncClient, seed_bulletin, editor_token):
    """Test deleting an announcement."""
    list_resp = await client.get("/api/v1/bulletins/2026-01-24/announcements")
    ann_id = list_resp.json()["data"][0]["id"]

    response = await client.delete(
        f"/api/v1/bulletins/2026-01-24/announcements/{ann_id}",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 204
