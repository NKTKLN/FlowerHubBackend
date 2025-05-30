from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from app.api.v1.order import OrderAPI
from app.schemas import CreateOrder, FlowerOrderItem, OrderResponse

order_api = OrderAPI()


@pytest.fixture
def app():
    from app.core import verify_token

    app = FastAPI()
    app.include_router(order_api.router, prefix="/api")

    async def override_token():
        return 1  # user_id

    app.dependency_overrides[verify_token] = override_token
    return app


@pytest.fixture
def sample_order_data():
    return CreateOrder(
        items=[
            OrderResponse(flower_id=1, quantity=2),
            OrderResponse(flower_id=2, quantity=3),
        ]
    )


@pytest.mark.asyncio
async def test_make_order_success():
    fake_user = SimpleNamespace(is_user_seller=False)
    order_items = [
        FlowerOrderItem(flower_id=1, quantity=2),
        FlowerOrderItem(flower_id=2, quantity=3),
    ]
    order_data = CreateOrder(items=order_items)

    fake_orders = [SimpleNamespace(id=123), SimpleNamespace(id=124)]

    with (
        patch("app.api.v1.order.get_user_by_id", new=AsyncMock(return_value=fake_user)),
        patch("app.api.v1.order.create_order_by_buyer", new=AsyncMock(return_value=fake_orders)),
    ):
        api = OrderAPI()

        response = await api.make_order(order_data=order_data, user_id=1, db=AsyncMock())
        assert response == {"details": "Заказ оформлен успешно"}


@pytest.mark.asyncio
async def test_make_order_forbidden(app, sample_order_data):
    fake_user = AsyncMock()
    fake_user.is_user_seller = True

    with patch("app.api.v1.order.get_user_by_id", return_value=fake_user):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/orders", json=sample_order_data.dict())

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "Доступ разрешён только покупателям"


# @pytest.mark.asyncio
# async def test_get_my_orders_success():
#     flower_1 = SimpleNamespace(id=1)
#     flower_2 = SimpleNamespace(id=2)

#     order_1 = SimpleNamespace(
#         id=10,
#         buyer_id=5,
#         order_date=date(2025, 5, 19),
#     )
#     rows = [
#         (1, 2, flower_1),
#         (2, 3, flower_2),
#     ]

#     seller_row = SimpleNamespace(seller_id=100)
#     mock_db = AsyncMock()

#     async def execute_side_effect(stmt):
#         class Result:
#             async def fetchall(self_):
#                 return rows

#             def first(self_):
#                 return seller_row

#         return Result()

#     mock_db.execute.side_effect = execute_side_effect

#     with (
#         patch(
#             "app.api.v1.order.get_user_by_id",
#             new=AsyncMock(return_value=SimpleNamespace(is_user_seller=False)),
#         ),
#         patch("app.api.v1.order.get_orders_by_buyer", new=AsyncMock(return_value=[order_1])),
#     ):
#         api = OrderAPI()

#         result = await api.get_my_orders(user_id=5, db=mock_db)
#         assert isinstance(result, list)
#         assert len(result) == 1
#         order_response = result[0]
#         assert isinstance(order_response, OrderResponse)
#         assert order_response.buyer_id == 5
#         assert order_response.order_id == 10
#         assert order_response.order_date == date(2025, 5, 19)
#         assert order_response.items == [
#             FlowerOrderItem(flower_id=1, quantity=2),
#             FlowerOrderItem(flower_id=2, quantity=3),
#         ]


@pytest.mark.asyncio
async def test_make_order_forbidden():
    from fastapi import HTTPException

    from app.schemas import CreateOrder

    order_data = CreateOrder(items=[FlowerOrderItem(flower_id=1, quantity=1)])

    with patch(
        "app.api.v1.order.get_user_by_id", return_value=SimpleNamespace(is_user_seller=True)
    ):
        from app.api.v1.order import OrderAPI

        api = OrderAPI()
        try:
            await api.make_order(order_data=order_data, user_id=1, db=AsyncMock())
        except HTTPException as e:
            assert e.status_code == 403
