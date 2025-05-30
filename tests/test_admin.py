from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.api.v1.admin import AdminAPI
from app.schemas import FlowerCreate, OrderSchema, UserData, UserRegister


@pytest.fixture
def app():
    api = AdminAPI()
    app = FastAPI()
    app.include_router(api.router, prefix="/admin")

    async def override_verify_token():
        return 1

    from app.core import verify_token

    app.dependency_overrides[verify_token] = override_verify_token
    return app


@pytest.mark.asyncio
async def test_create_user_success(app):
    user_register = UserRegister(
        email="test@example.com", first_name="Test", last_name="User", password="pass"
    )
    created_user = UserData(
        id=1,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        display_name="Test User",
        is_user_seller=False,
        is_user_admin=False,
        address=None,
    )

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_execute = AsyncMock(return_value=mock_result)

    with (
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_execute),
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
        patch(
            "app.api.v1.admin.create_user", new=AsyncMock(return_value=MagicMock(id=1))
        ) as mock_create_user,
        patch(
            "app.api.v1.admin.get_user_by_id", new=AsyncMock(return_value=created_user)
        ) as mock_get_user_by_id,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/admin/users", json=user_register.dict())

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        mock_check_admin.assert_awaited_once()
        mock_create_user.assert_awaited_once()
        mock_get_user_by_id.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user_email_exists(app):
    user_register = UserRegister(
        email="exists@example.com", first_name="Test", last_name="User", password="pass"
    )

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = True
    mock_result.scalars.return_value = mock_scalars
    mock_execute = AsyncMock(return_value=mock_result)

    with (
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_execute),
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/admin/users", json=user_register.dict())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Пользователь с таким email уже существует"
        mock_check_admin.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_success(app):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = True  # user found
    mock_result.scalars.return_value = mock_scalars
    mock_execute = AsyncMock(return_value=mock_result)
    mock_commit = AsyncMock()

    with (
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_execute),
        patch("sqlalchemy.ext.asyncio.AsyncSession.commit", mock_commit),
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/admin/users/1")

        assert response.status_code == 200
        assert "удалён" in response.json()["detail"]
        mock_check_admin.assert_awaited_once()
        mock_execute.assert_awaited()
        mock_commit.assert_awaited()


@pytest.mark.asyncio
async def test_delete_user_not_found(app):
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars
    mock_execute = AsyncMock(return_value=mock_result)
    mock_commit = AsyncMock()

    with (
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_execute),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/admin/users/9999")
        print(response.text)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Пользователь не найден"
        mock_check_admin.assert_awaited_once()


@pytest.mark.asyncio
async def test_admin_update_user_success(app):
    updated_user = UserData(
        id=1,
        email="updated@example.com",
        first_name="Updated",
        last_name="User",
        display_name="Updated User",
        is_user_seller=False,
        is_user_admin=True,
        address=None,
    )
    with (
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
        patch(
            "app.api.v1.admin.get_user_by_id",
            new=AsyncMock(side_effect=[updated_user, updated_user]),
        ) as mock_get_user_by_id,
        patch("app.api.v1.admin.update_user", new=AsyncMock()) as mock_update_user,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put("/admin/users/1", json=updated_user.dict())

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated@example.com"
        mock_check_admin.assert_awaited_once()
        mock_update_user.assert_awaited_once()
        assert mock_get_user_by_id.await_count == 2


@pytest.mark.asyncio
async def test_admin_update_user_not_found(app):
    updated_user = UserData(
        id=999,
        email="notfound@example.com",
        first_name="No",
        last_name="User",
        display_name="No User",
        is_user_seller=False,
        is_user_admin=False,
        address=None,
    )
    with (
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
        patch(
            "app.api.v1.admin.get_user_by_id", new=AsyncMock(return_value=None)
        ) as mock_get_user_by_id,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put("/admin/users/999", json=updated_user.dict())

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Пользователь не найден"
        mock_check_admin.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_users_success(app):
    user = MagicMock(id=1, email="test@example.com")
    person = MagicMock(first_name="Test", last_name="User", display_name="Test User")
    user_type = MagicMock(id=1, name="Админ")

    mock_result = MagicMock()
    mock_result.all = AsyncMock(return_value=[(user, person, user_type)])

    mock_execute = AsyncMock(return_value=mock_result)

    with (
        patch("sqlalchemy.ext.asyncio.AsyncSession.execute", mock_execute),
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/admin/users")

        assert response.status_code == 200
        users = response.json()
        assert len(users) == 1
        assert users[0]["email"] == "test@example.com"
        assert users[0]["is_user_admin"] is True
        mock_check_admin.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_flower_success(app):
    flower_data = FlowerCreate(
        name="Rose",
        type_id=1,
        season_id=1,
        usage_id=1,
        country_id=1,
        variety="Beautiful",
        price=10.0,
    )
    flower_return = MagicMock()
    flower_return.id = 1
    flower_return.name = flower_data.name
    flower_return.variety = flower_data.variety
    flower_return.price = flower_data.price

    with (
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
        patch(
            "app.api.v1.admin.create_flower", new=AsyncMock(return_value=flower_return)
        ) as mock_create_flower,
        patch("app.api.v1.admin.add_flower_to_seller", new=AsyncMock()) as mock_add_flower,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/admin/flowers", json=flower_data.dict(), params={"seller_id": 1}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == flower_data.name
        mock_check_admin.assert_awaited_once()
        mock_create_flower.assert_awaited_once()
        mock_add_flower.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_users_success(app):
    user = MagicMock(id=1, email="test@example.com")
    person = MagicMock(first_name="Test", last_name="User", display_name="Test User")
    user_type = MagicMock()
    user_type.name = "Админ"

    mock_result = MagicMock()
    mock_result.all.return_value = [(user, person, user_type)]

    with (
        patch("app.api.v1.admin.AdminAPI._check_admin", new=AsyncMock()) as mock_check_admin,
        patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute", new=AsyncMock(return_value=mock_result)
        ) as mock_execute,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/admin/users")

        assert response.status_code == 200
        users = response.json()
        print(users)
        assert len(users) == 1
        assert users[0]["email"] == "test@example.com"
        assert users[0]["is_user_admin"] is True
        mock_check_admin.assert_awaited_once()
