from unittest.mock import ANY, AsyncMock, patch

import pytest
from fastapi import status
from httpx import ASGITransport, AsyncClient

from app.api.v1.user import UserAPI
from app.schemas import UserData

user_api = UserAPI()


@pytest.fixture
def app():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(user_api.router, prefix="/user")

    async def override_verify_token():
        return "123"

    from app.core import verify_token

    app.dependency_overrides[verify_token] = override_verify_token

    return app


@pytest.fixture
def test_user_data():
    return UserData(
        id=0,
        first_name="user",
        last_name="user",
        display_name="user",
        email="test@example.com",
        is_user_seller=True,
        is_user_admin=False,
        address=None,
    )


@pytest.mark.asyncio
async def test_get_user_success(app, test_user_data):
    with (
        patch("app.api.v1.user.get_user_by_id", new_callable=AsyncMock) as mock_get_user,
    ):
        mock_get_user.return_value = test_user_data
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/user/", headers={"X-Token": "test-token"})

        assert response.status_code == 200
        assert response.json()["display_name"] == "user"
        mock_get_user.assert_awaited_once_with(ANY, "123")


@pytest.mark.asyncio
async def test_get_user_not_found(app):
    with (
        patch("app.api.v1.user.get_user_by_id", new_callable=AsyncMock) as mock_get_user,
    ):
        mock_get_user.return_value = None
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/user/", headers={"X-Token": "test-token"})

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert response.json()["detail"] == "Данные пользователя недействительны"
        mock_get_user.assert_awaited_once_with(ANY, "123")


@pytest.mark.asyncio
async def test_update_user_data(app, test_user_data):
    with (
        patch("app.api.v1.user.update_user", new_callable=AsyncMock) as mock_update_user,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(
                "/user/", json=test_user_data.dict(), headers={"X-Token": "test-token"}
            )

        assert response.status_code == 200
        assert response.json()["detail"] == "Данные пользователя успешно обновлены"
        mock_update_user.assert_awaited_once_with(ANY, "123", test_user_data)


@pytest.mark.asyncio
async def test_update_user_password(app):
    with (
        patch("app.api.v1.user.update_password", new_callable=AsyncMock) as mock_update_password,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(
                "/user/password?new_password=newpassword123", headers={"X-Token": "test-token"}
            )
        print(response.text)
        assert response.status_code == 200
        assert response.json()["detail"] == "Данные пользователя успешно обновлены"
        mock_update_password.assert_awaited_once_with(ANY, "123", "newpassword123")


@pytest.mark.asyncio
async def test_get_user_by_id_success(app, test_user_data):
    with (
        patch("app.api.v1.user.get_user_by_id", new_callable=AsyncMock) as mock_get_user,
        patch("app.api.v1.user.auth_service.decode_token", return_value={"sub": "123"}),
    ):
        mock_get_user.side_effect = [test_user_data, test_user_data]  # get_user_data и user_data

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/user/0", headers={"X-Token": "test-token"})

        assert response.status_code == 200
        assert response.json()["display_name"] == "user"
        assert mock_get_user.call_count == 2


@pytest.mark.asyncio
async def test_get_user_by_id_forbidden(app, test_user_data):
    unauthorized_user = UserData(
        id=123,
        first_name="unauth",
        last_name="user",
        display_name="unauth",
        email="unauth@example.com",
        is_user_seller=False,
        is_user_admin=False,
        address=None,
    )

    requested_user = UserData(
        id=0,
        first_name=" requested",
        last_name=" requested",
        display_name=" requested",
        email=" requested@example.com",
        is_user_seller=False,
        is_user_admin=False,
        address=None,
    )

    with (
        patch("app.api.v1.user.get_user_by_id", new_callable=AsyncMock) as mock_get_user,
        patch("app.api.v1.user.auth_service.decode_token", return_value={"sub": "123"}),
    ):
        mock_get_user.side_effect = [unauthorized_user, requested_user]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/user/0", headers={"X-Token": "test-token"})

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert response.json()["detail"] == "Отказано в доступе"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(app):
    with (
        patch("app.api.v1.user.get_user_by_id", new_callable=AsyncMock) as mock_get_user,
        patch("app.api.v1.user.auth_service.decode_token", return_value={"sub": "123"}),
    ):
        mock_get_user.side_effect = [None, None]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/user/0", headers={"X-Token": "test-token"})

        assert response.status_code == status.HTTP_502_BAD_GATEWAY
        assert response.json()["detail"] == "Данные пользователя недействительны"
