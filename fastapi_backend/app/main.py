from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db.database import Base, engine
from .routers.admin import router as admin_router
from .routers.auth_routes import router as auth_router
from .routers.exams import router as exams_router
from .routers.users import router as users_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as db:
        await db.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Rhytmic Exam API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(exams_router)
app.include_router(admin_router)