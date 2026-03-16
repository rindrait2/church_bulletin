import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_programs_grouped(client: AsyncClient, seed_bulletin):
    """Test listing programs returns items grouped by block."""
    response = await client.get("/api/v1/bulletins/2026-01-24/programs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "lessonStudy" in data["data"]
    assert "ssProgram" in data["data"]
    assert "divineService" in data["data"]
    assert len(data["data"]["lessonStudy"]) >= 1


@pytest.mark.asyncio
async def test_create_program(client: AsyncClient, seed_bulletin, editor_token):
    """Test creating a program item."""
    response = await client.post(
        "/api/v1/bulletins/2026-01-24/programs",
        json={"block": "divine_service", "sequence": 99, "role": "Test Role", "person": "Test Person"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["role"] == "Test Role"


@pytest.mark.asyncio
async def test_reorder_programs(client: AsyncClient, seed_bulletin, editor_token):
    """Test reordering program items."""
    # First get current items
    list_resp = await client.get("/api/v1/bulletins/2026-01-24/programs")
    items = list_resp.json()["data"]["divineService"]
    if len(items) >= 2:
        reorder_data = [
            {"id": items[0]["id"], "sequence": 100},
            {"id": items[1]["id"], "sequence": 101},
        ]
        response = await client.patch(
            "/api/v1/bulletins/2026-01-24/programs/reorder",
            json=reorder_data,
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
