from contextlib import asynccontextmanager
import time
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.api.v1 import AdminAPI, AuthAPI, FlowerAPI, OrderAPI, SellerAPI, UserAPI
from app.core import setup_logger
from app.crud import create_admin
from app.db.database import get_session, init_db
from app.schemas import UserRegister
import logging
from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logger()
    await init_db()

    async for session in get_session():
        await create_admin(
            session,
            UserRegister(
                email="test@admin.ti",
                first_name="test@admin.ti",
                last_name="test@admin.ti",
                password="test@admin.ti",
            ),
        )

    yield
THRESHOLD_MS = 300



app = FastAPI(title="FlowerHub API", lifespan=lifespan)

@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = time.monotonic()
    response = await call_next(request)
    duration_ms = (time.monotonic() - start_time) * 1000
    if duration_ms > THRESHOLD_MS:
        logger.warning(f"Длительный отклик: {duration_ms:.2f} мс, путь: {request.url.path}")
    return response


@app.get("/", include_in_schema=False)
async def root_redirect():
    return RedirectResponse(url="/docs")


auth = AuthAPI()
user = UserAPI()
flower = FlowerAPI()
seller = SellerAPI()
order = OrderAPI()
admin = AdminAPI()

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(user.router, prefix="/api/v1/user", tags=["user"])
app.include_router(flower.router, prefix="/api/v1/flowers", tags=["flower"])
app.include_router(seller.router, prefix="/api/v1/seller", tags=["seller"])
app.include_router(order.router, prefix="/api/v1/order", tags=["order"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
