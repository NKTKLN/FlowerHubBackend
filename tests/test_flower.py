from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.api.v1.flower import FlowerAPI
from app.schemas import (
    FlowerData,
    FloweringcountriesData,
    FloweringSeasonData,
    FlowerTypeData,
    FlowerUsageData,
)

flower_api = FlowerAPI()


@pytest.fixture
def app():
    from app.core import verify_token

    app = FastAPI()
    app.include_router(flower_api.router, prefix="/flowers")

    async def override_verify_token():
        return "123"

    app.dependency_overrides[verify_token] = override_verify_token
    return app


@pytest.fixture
def fake_flower_data():
    return [
        FlowerData(
            id=1,
            name="Rose",
            type_id=1,
            season_id=1,
            usage_id=1,
            country_id=1,
            variety="Hybrid Tea",
            price=10.5,
        ),
        FlowerData(
            id=2,
            name="Tulip",
            type_id=2,
            season_id=2,
            usage_id=2,
            country_id=2,
            variety="Darwin Hybrid",
            price=8.0,
        ),
    ]


@pytest.mark.asyncio
async def test_list_flowers_success(app, fake_flower_data):
    with patch("app.api.v1.flower.get_flowers", new_callable=AsyncMock) as mock_get_flowers:
        mock_get_flowers.return_value = fake_flower_data

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/flowers/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Rose"
        assert data[1]["name"] == "Tulip"
        mock_get_flowers.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_flowers_with_filters(app):
    with patch("app.api.v1.flower.get_flowers", new_callable=AsyncMock) as mock_get_flowers:
        mock_get_flowers.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/flowers/?name=Rose&min_price=5&max_price=15")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
        mock_get_flowers.assert_awaited_once()
        filters = mock_get_flowers.call_args[0][1]
        assert filters.name == "Rose"
        assert filters.min_price == 5
        assert filters.max_price == 15


@pytest.mark.asyncio
async def test_list_flowers_pagination(app):
    with patch("app.api.v1.flower.get_flowers", new_callable=AsyncMock) as mock_get_flowers:
        mock_get_flowers.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/flowers/?limit=10&offset=20")

        kwargs = mock_get_flowers.call_args.kwargs
        assert kwargs["limit"] == 10
        assert kwargs["offset"] == 20


@pytest.mark.asyncio
async def test_list_flowers_empty_result(app):
    with patch("app.api.v1.flower.get_flowers", new_callable=AsyncMock) as mock_get_flowers:
        mock_get_flowers.return_value = []

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/flowers/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
        mock_get_flowers.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_flowers_invalid_query(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/flowers/?limit=200&min_price=-5"
        )  # invalid: limit > 100, min_price < 0

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_list_flowers_internal_server_error(app):
    with patch("app.api.v1.flower.get_flowers", new_callable=AsyncMock) as mock_get_flowers:
        mock_get_flowers.side_effect = Exception("Unexpected error")

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/flowers/")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert data["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_create_flower_type_success(app):
    payload = {"name": "Test Type", "description": "Test Description"}

    with (
        patch("app.api.v1.flower.create_flower_type", new_callable=AsyncMock) as mock_create,
        patch("app.api.v1.flower.get_user_by_id", new_callable=AsyncMock) as mock_user,
    ):
        mock_create.return_value = {"id": 1, "name": "Test Type", "description": "Test Description"}
        mock_user.return_value = type("User", (), {"is_user_seller": True, "is_user_admin": False})

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/flowers/types", json=payload, headers={"X-Token": "test-token"}
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Type"
        mock_create.assert_awaited_once()
