from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.models.database import engine, Base
from app.api import auth, chat, testcase, execution, git

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging
    logger = logging.getLogger(__name__)

    if settings.JWT_SECRET == "change-me-in-production":
        logger.warning(
            "JWT_SECRET is using the default value! "
            "Set a strong secret in .env for production."
        )

    # In production, use `alembic upgrade head` instead of create_all.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    from app.services.executor_client import close_client
    await close_client()
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(testcase.router)
app.include_router(execution.router)
app.include_router(git.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
