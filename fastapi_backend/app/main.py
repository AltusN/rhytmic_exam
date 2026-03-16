from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .db.database import get_db, Base, engine
from .db import models
from .schemas import UserCreate, UserRead
from passlib.context import CryptContext

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as db:
        await db.run_sync(models.Base.metadata.create_all)

def get_password_hash(password):
    return pwd_context.hash(password)

@app.post("/users/", response_model=UserRead)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = models.User(
        username=user.username,
        name=user.name,
        surname=user.surname,
        sagf_id=user.sagf_id,
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user