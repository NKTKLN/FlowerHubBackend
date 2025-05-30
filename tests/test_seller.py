from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.schemas import (
    FlowerCreate,
    FloweringSeasonCreate,
    FlowerTypeCreate,
    FlowerUpdate,
    FlowerUsageCreate,
)


@pytest.mark.asyncio
async def test_add_flower_success():
    flower_data = FlowerCreate(
        name="Rose", type_id=1, season_id=1, usage_id=1, variety="Red", price=10.5, country_id=1
    )

    mock_user = AsyncMock()
    mock_user.is_user_seller = True
    mock_flower = AsyncMock(id=123)

    with (
        patch("app.api.v1.seller.get_user_by_id", new=AsyncMock(return_value=mock_user)),
        patch("app.api.v1.seller.create_flower", new=AsyncMock(return_value=mock_flower)),
    ):
        from app.api.v1.seller import SellerAPI

        api = SellerAPI()

        result = await api.add_flower(flower_data, user_id=1, db=AsyncMock())
        assert result.id == 123


@pytest.mark.asyncio
async def test_add_flower_forbidden():
    flower_data = FlowerCreate(
        name="Rose", type_id=1, season_id=1, usage_id=1, variety="Red", price=10.5, country_id=1
    )

    mock_user = AsyncMock()
    mock_user.is_user_seller = False
    mock_user.is_user_admin = False

    with patch("app.api.v1.seller.get_user_by_id", new=AsyncMock(return_value=mock_user)):
        from app.api.v1.seller import SellerAPI

        api = SellerAPI()

        with pytest.raises(HTTPException) as exc:
            await api.add_flower(flower_data, user_id=1, db=AsyncMock())
        assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_edit_flower_success():
    flower_update = FlowerUpdate(name="Tulip", price=12.0)
    mock_user = AsyncMock()
    mock_user.is_user_seller = True
    mock_updated_flower = AsyncMock(id=42)

    with (
        patch("app.api.v1.seller.get_user_by_id", new=AsyncMock(return_value=mock_user)),
        patch("app.api.v1.seller.update_flower", new=AsyncMock(return_value=mock_updated_flower)),
    ):
        from app.api.v1.seller import SellerAPI

        api = SellerAPI()

        result = await api.edit_flower(42, flower_update, user_id=1, db=AsyncMock())
        assert result.id == 42


@pytest.mark.asyncio
async def test_remove_flower_success():
    mock_user = AsyncMock()
    mock_user.is_user_seller = True

    with (
        patch("app.api.v1.seller.get_user_by_id", new=AsyncMock(return_value=mock_user)),
        patch("app.api.v1.seller.delete_flower", new=AsyncMock(return_value=None)),
    ):
        from app.api.v1.seller import SellerAPI

        api = SellerAPI()

        result = await api.remove_flower(42, user_id=1, db=AsyncMock())
        assert result == {"detail": "Цветок удалён успешно"}


@pytest.mark.asyncio
async def test_get_orders_success():
    mock_user = AsyncMock()
    mock_user.is_user_buyer = True
    fake_orders = [AsyncMock(id=1), AsyncMock(id=2)]

    with (
        patch("app.api.v1.seller.get_user_by_id", new=AsyncMock(return_value=mock_user)),
        patch("app.api.v1.seller.get_orders_by_seller", new=AsyncMock(return_value=fake_orders)),
    ):
        from app.api.v1.seller import SellerAPI

        api = SellerAPI()

        orders = await api.get_orders(user_id=1, db=AsyncMock())
        assert len(orders) == 2


@pytest.mark.asyncio
async def test_get_orders_forbidden():
    mock_user = AsyncMock()
    mock_user.is_user_seller = False
    mock_user.is_user_admin = False

    with (
        patch("app.api.v1.seller.get_user_by_id", new=AsyncMock(return_value=mock_user)),
        patch("app.api.v1.seller.get_orders_by_seller", new=AsyncMock()) as mock_get_orders,
    ):
        mock_get_orders.return_value = []

        from app.api.v1.seller import SellerAPI

        api = SellerAPI()

        with pytest.raises(HTTPException) as exc:
            await api.get_orders(user_id=1, db=AsyncMock())
        assert exc.value.status_code == 403
