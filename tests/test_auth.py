import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, seed_users):
    """Test successful login returns tokens."""
    response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_fail(client: AsyncClient, seed_users):
    """Test login with wrong password returns 401."""
    response = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient, seed_users):
    """Test refreshing an access token."""
    login = await client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    refresh_token = login.json()["data"]["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "access_token" in response.json()["data"]


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient):
    """Test accessing /me without a token returns 401."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient, admin_token):
    """Test accessing /me with a valid token returns user info."""
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "admin"
    assert data["data"]["role"] == "admin"


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, admin_token):
    """Test registering a new user as admin."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "password": "pass123", "role": "viewer"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["username"] == "newuser"
    assert response.json()["data"]["role"] == "viewer"


@pytest.mark.asyncio
async def test_register_requires_admin(client: AsyncClient, editor_token):
    """Test that editors cannot register users."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "blocked", "password": "pass123"},
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, admin_token):
    """Test registering a duplicate username returns 409."""
    await client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "password": "pass123"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": "dupuser", "password": "pass456"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, seed_users):
    """Test changing own password."""
    login = await client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    token = login.json()["data"]["access_token"]

    response = await client.put(
        "/api/v1/auth/password",
        json={"current_password": "editor123", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify new password works
    login2 = await client.post("/api/v1/auth/login", json={"username": "editor", "password": "newpass123"})
    assert login2.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, admin_token):
    """Test changing password with wrong current password fails."""
    response = await client.put(
        "/api/v1/auth/password",
        json={"current_password": "wrongpass", "new_password": "newpass123"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, admin_token):
    """Test listing users as admin."""
    response = await client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert len(response.json()["data"]) >= 2


@pytest.mark.asyncio
async def test_update_user_role(client: AsyncClient, admin_token):
    """Test updating a user's role as admin."""
    # Get users list to find editor's ID
    users_resp = await client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {admin_token}"})
    editor = next(u for u in users_resp.json()["data"] if u["username"] == "editor")

    response = await client.put(
        f"/api/v1/auth/users/{editor['id']}",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "admin"
