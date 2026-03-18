from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .db.database import get_db, Base, engine
from .db import models
from .schemas import UserCreate, UserRead
import bcrypt

app = FastAPI()
BCRYPT_MAX_PASSWORD_BYTES = 72

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as db:
        await db.run_sync(models.Base.metadata.create_all)

def get_password_hash(password):
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(
            f"Password is too long for bcrypt (max {BCRYPT_MAX_PASSWORD_BYTES} bytes in UTF-8)."
        )
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")

@app.post("/users/", response_model=UserRead)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        hashed_password = get_password_hash(user.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db_user = models.User(
        username=user.username,
        name=user.name,
        surname=user.surname,
        sagf_id=user.sagf_id,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user