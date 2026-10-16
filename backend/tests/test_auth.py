import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration returning 201 Created and user profile."""
    payload = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert isinstance(data["id"], int)
    assert data["id"] > 0
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert data["is_admin"] is False
    assert "created_at" in data
    # Ensure sensitive credential data is never leaked
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_email_normalization(client: AsyncClient):
    """Test that email normalization trims whitespace and downcases letters."""
    payload = {
        "email": "  NORMALIZED.User@Example.COM  ",
        "full_name": "Normalized User",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["email"] == "normalized.user@example.com"


@pytest.mark.asyncio
async def test_case_insensitive_duplicate_email_rejection(client: AsyncClient):
    """Test that registering duplicate emails with different casing returns HTTP 400."""
    initial_user = {
        "email": "USER@domain.com",
        "full_name": "Initial User",
        "password": "Password123!",
    }
    first_res = await client.post("/api/auth/register", json=initial_user)
    assert first_res.status_code == 201

    duplicate_user = {
        "email": "user@DOMAIN.COM",
        "full_name": "Duplicate User",
        "password": "AnotherPassword123!",
    }
    dup_res = await client.post("/api/auth/register", json=duplicate_user)
    assert dup_res.status_code == 400
    assert dup_res.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_bcrypt_72_byte_password_validation(client: AsyncClient):
    """Test that passwords exceeding 72 UTF-8 bytes are rejected with HTTP 422."""
    # 72 ASCII bytes: boundary check, exactly at limit
    valid_72_payload = {
        "email": "valid72@example.com",
        "full_name": "Valid 72",
        "password": "P" * 72,
    }
    valid_res = await client.post("/api/auth/register", json=valid_72_payload)
    assert valid_res.status_code == 201

    # 73 ASCII bytes (> 72 bytes): must be rejected with 422
    over_72_ascii = {
        "email": "over72ascii@example.com",
        "full_name": "Over 72 ASCII",
        "password": "P" * 73,
    }
    over_res1 = await client.post("/api/auth/register", json=over_72_ascii)
    assert over_res1.status_code == 422
    assert "Password must be at most 72 bytes" in over_res1.text

    # Multi-byte UTF-8 string exceeding 72 bytes (25 chars of 3-byte '€' = 75 bytes)
    over_72_unicode = {
        "email": "over72unicode@example.com",
        "full_name": "Over 72 Unicode",
        "password": "€" * 25,
    }
    over_res2 = await client.post("/api/auth/register", json=over_72_unicode)
    assert over_res2.status_code == 422
    assert "Password must be at most 72 bytes" in over_res2.text


@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient, user_factory):
    """Test that login with incorrect password returns HTTP 401 Unauthorized."""
    await user_factory(
        email="login_fail@example.com",
        password="CorrectPassword123!",
        full_name="Login Fail User",
    )

    response = await client.post(
        "/api/auth/login",
        data={
            "username": "login_fail@example.com",
            "password": "WrongPassword456!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
    assert "Bearer" in response.headers.get("WWW-Authenticate", "")


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test that login with a non-existent email returns HTTP 401 Unauthorized."""
    response = await client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "AnyPassword123!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


@pytest.mark.asyncio
async def test_successful_login_and_me_profile_retrieval(client: AsyncClient, user_factory):
    """Test successful login returns access token and /api/auth/me returns profile."""
    user = await user_factory(
        email="alice@example.com",
        password="SecurePassword123!",
        full_name="Alice Wonderland",
    )

    # Login with case-insensitive email username
    login_res = await client.post(
        "/api/auth/login",
        data={
            "username": "ALICE@EXAMPLE.COM",
            "password": "SecurePassword123!",
        },
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["id"] == user.id
    assert login_data["user"]["email"] == "alice@example.com"
    assert login_data["user"]["full_name"] == "Alice Wonderland"
    assert login_data["user"]["is_active"] is True
    assert login_data["user"]["is_admin"] is False

    token = login_data["access_token"]

    # Retrieve profile via /api/auth/me
    me_res = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user.id
    assert me_data["email"] == "alice@example.com"
    assert me_data["full_name"] == "Alice Wonderland"
    assert me_data["is_active"] is True
    assert me_data["is_admin"] is False


@pytest.mark.asyncio
async def test_me_unauthorized_without_token(client: AsyncClient):
    """Test that /api/auth/me returns HTTP 401 when no token or invalid token is supplied."""
    no_token_res = await client.get("/api/auth/me")
    assert no_token_res.status_code == 401

    invalid_token_res = await client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.token.payload"},
    )
    assert invalid_token_res.status_code == 401


@pytest.mark.asyncio
async def test_deactivated_user_protection(
    client: AsyncClient,
    db_session: AsyncSession,
    user_factory,
):
    """Test that deactivated users cannot retrieve profile with existing token or login."""
    user = await user_factory(
        email="deactivated@example.com",
        password="UserPassword123!",
        full_name="Deactivated User",
        is_active=True,
    )

    # Obtain valid access token while user is active
    login_res = await client.post(
        "/api/auth/login",
        data={
            "username": "deactivated@example.com",
            "password": "UserPassword123!",
        },
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Verify /api/auth/me works while active
    me_res_active = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res_active.status_code == 200

    # Deactivate user in database
    user.is_active = False
    db_session.add(user)
    await db_session.commit()

    # 1. Existing token must return 403 Forbidden with "Account is deactivated"
    me_res_deactivated = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res_deactivated.status_code == 403
    assert me_res_deactivated.json()["detail"] == "Account is deactivated"

    # 2. Attempting a new login must return 403 Forbidden with "Account is deactivated"
    login_res_deactivated = await client.post(
        "/api/auth/login",
        data={
            "username": "deactivated@example.com",
            "password": "UserPassword123!",
        },
    )
    assert login_res_deactivated.status_code == 403
    assert login_res_deactivated.json()["detail"] == "Account is deactivated"


@pytest.mark.asyncio
async def test_create_admin_script_create_and_upgrade(db_session: AsyncSession):
    """Test standalone create_admin script validation, creation, and existing user promotion."""
    from app.scripts.create_admin import validate_credentials, create_or_upgrade_admin

    with pytest.raises(ValueError, match="Invalid email"):
        validate_credentials("invalid-email", "ValidPass123!")

    with pytest.raises(ValueError, match="at least 8 characters"):
        validate_credentials("admin@example.com", "short")

    with pytest.raises(ValueError, match="at most 72 bytes"):
        validate_credentials("admin@example.com", "A" * 73)

    # Create new admin user
    admin_user, created = await create_or_upgrade_admin(
        email="  CLI_Admin@Example.com ",
        password="StrongAdminPassword123!",
        full_name="CLI Admin",
        session=db_session,
    )
    assert created is True
    assert admin_user.email == "cli_admin@example.com"
    assert admin_user.is_admin is True
    assert admin_user.is_active is True

    # Demote/deactivate and verify upgrade path promotes back to active admin
    admin_user.is_admin = False
    admin_user.is_active = False
    await db_session.commit()

    upgraded_user, created_again = await create_or_upgrade_admin(
        email="cli_admin@example.com",
        password="StrongAdminPassword123!",
        session=db_session,
    )
    assert created_again is False
    assert upgraded_user.id == admin_user.id
    assert upgraded_user.is_admin is True
    assert upgraded_user.is_active is True


@pytest.mark.asyncio
async def test_admin_endpoints_rbac_and_operations(
    client: AsyncClient,
    test_user,
    test_admin_user,
    auth_headers: dict,
    admin_auth_headers: dict,
):
    """Test /api/admin/* endpoints enforce RBAC and properly manage users and stats."""
    # Non-admin user receives 403 Forbidden
    forbidden_res = await client.get("/api/admin/stats", headers=auth_headers)
    assert forbidden_res.status_code == 403

    # Admin can fetch stats
    stats_res = await client.get("/api/admin/stats", headers=admin_auth_headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_users"] >= 2
    assert stats["admin_users"] >= 1

    # Admin can list users
    users_res = await client.get("/api/admin/users", headers=admin_auth_headers)
    assert users_res.status_code == 200
    assert len(users_res.json()) >= 2

    # Admin cannot deactivate, demote, or delete themselves
    self_deact = await client.patch(
        f"/api/admin/users/{test_admin_user.id}/toggle-active",
        headers=admin_auth_headers,
    )
    assert self_deact.status_code == 400

    self_demote = await client.patch(
        f"/api/admin/users/{test_admin_user.id}/toggle-admin",
        headers=admin_auth_headers,
    )
    assert self_demote.status_code == 400

    self_delete = await client.delete(
        f"/api/admin/users/{test_admin_user.id}",
        headers=admin_auth_headers,
    )
    assert self_delete.status_code == 400

    # Admin can toggle active and admin status on another user, then delete them
    toggle_act = await client.patch(
        f"/api/admin/users/{test_user.id}/toggle-active",
        headers=admin_auth_headers,
    )
    assert toggle_act.status_code == 200
    assert toggle_act.json()["is_active"] is False

    toggle_adm = await client.patch(
        f"/api/admin/users/{test_user.id}/toggle-admin",
        headers=admin_auth_headers,
    )
    assert toggle_adm.status_code == 200
    assert toggle_adm.json()["is_admin"] is True

    del_res = await client.delete(
        f"/api/admin/users/{test_user.id}",
        headers=admin_auth_headers,
    )
    assert del_res.status_code == 204

