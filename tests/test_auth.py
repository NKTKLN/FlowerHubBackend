from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_user_success():
    user_data = {
        "email": "test@example.com",
        "password": "password123",
        "first_name": "string",
        "last_name": "string",
        "is_user_seller": False,
    }

    with (
        patch("app.api.v1.auth.get_user_by_email", new_callable=AsyncMock) as mock_get_user,
        patch("app.api.v1.auth.create_user", new_callable=AsyncMock) as mock_create_user,
        patch("app.core.auth_service.create_access_token") as mock_access_token,
        patch("app.core.auth_service.create_refresh_token") as mock_refresh_token,
    ):
        mock_get_user.return_value = None
        fake_user = AsyncMock()
        fake_user.id = 1
        mock_create_user.return_value = fake_user

        mock_access_token.return_value = "access_token"
        mock_refresh_token.return_value = "refresh_token"

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


def test_register_user_existing_email():
    user_data = {
        "email": "exists@example.com",
        "password": "password123",
        "first_name": "string",
        "last_name": "string",
        "is_user_seller": False,
    }

    with patch("app.api.v1.auth.get_user_by_email", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = AsyncMock()  # возвращаем фейкового пользователя

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "User with this email already exists"


def test_login_success():
    user_data = {"email": "test@example.com", "password": "password123"}

    fake_user = AsyncMock()
    fake_user.id = 1
    fake_user.password_hash = "hashed_password"

    with (
        patch("app.crud.get_user_by_email", new_callable=AsyncMock) as mock_get_user,
        patch("app.core.auth_service.verify_password") as mock_verify_password,
        patch("app.core.auth_service.create_access_token") as mock_access_token,
        patch("app.core.auth_service.create_refresh_token") as mock_refresh_token,
    ):
        mock_get_user.return_value = fake_user
        mock_verify_password.return_value = True
        mock_access_token.return_value = "access_token"
        mock_refresh_token.return_value = "refresh_token"

        response = client.post("/api/v1/auth/login", json=user_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data


def test_login_wrong_password():
    user_data = {"email": "test@example.com", "password": "wrong_password"}

    fake_user = AsyncMock()
    fake_user.password_hash = "hashed_password"

    with (
        patch("app.crud.get_user_by_email", new_callable=AsyncMock) as mock_get_user,
        patch("app.core.auth_service.verify_password") as mock_verify_password,
    ):
        mock_get_user.return_value = fake_user
        mock_verify_password.return_value = False

        response = client.post("/api/v1/auth/login", json=user_data)

        assert response.status_code == 400
        assert response.json()["detail"] == "Incorrect username or password"


def test_refresh_token_success():
    fake_payload = {"sub": "1"}

    with (
        patch("app.core.auth_service.decode_token") as mock_decode_token,
        patch("app.core.auth_service.is_token_revoked") as mock_is_revoked,
        patch("app.core.auth_service.create_access_token") as mock_create_access_token,
        patch("app.core.auth_service.create_refresh_token") as mock_create_refresh_token,
        patch("app.core.auth_service.revoke_token") as mock_revoke_token,
    ):
        mock_decode_token.return_value = fake_payload
        mock_is_revoked.return_value = False
        mock_create_access_token.return_value = "new_access_token"
        mock_create_refresh_token.return_value = "new_refresh_token"
        mock_revoke_token.return_value = None

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "valid_refresh_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new_access_token"
        assert data["refresh_token"] == "new_refresh_token"


def test_refresh_token_invalid():
    with patch("app.core.auth_service.decode_token") as mock_decode_token:
        mock_decode_token.return_value = None

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid refresh token"


def test_refresh_token_revoked():
    fake_payload = {"sub": "1"}

    with (
        patch("app.core.auth_service.decode_token") as mock_decode_token,
        patch("app.core.auth_service.is_token_revoked") as mock_is_revoked,
    ):
        mock_decode_token.return_value = fake_payload
        mock_is_revoked.return_value = True

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "revoked_token"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Token revoked"
