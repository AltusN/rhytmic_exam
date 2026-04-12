import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import (
    create_access_token,
    create_reset_password_token,
    hash_password,
    verify_password,
    verify_reset_password_token,
)
from ..db.database import get_db
from ..db.models import User
from ..email import send_email
from ..schemas import (
    MessageResponse,
    ResetPasswordConfirm,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserRead,
)

router = APIRouter(tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not enabled")

    access_token = create_access_token(data={"sub": str(user.username)})
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/users/", response_model=UserRead, tags=["users"])
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)) -> UserRead:
    try:
        hashed_password = hash_password(user.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db_user = User(
        username=user.username.strip(),
        level=user.level,
        name=user.name.strip(),
        surname=user.surname.strip(),
        sagf_id=user.sagf_id.strip(),
        email=user.email.strip().lower(),
        hashed_password=hashed_password,
        enabled=True,
    )
    db.add(db_user)

    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Username, SAGF ID, or email already exists") from exc

    await db.refresh(db_user)
    return db_user


@router.post("/auth/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    return MessageResponse(message="Logout successful. Discard token on client.")


@router.post("/auth/reset-password-request", response_model=MessageResponse)
async def reset_password_request(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if user:
        token = create_reset_password_token(user.id)
        reset_link = f"/auth/reset-password?token={token}"
        send_email(
            subject="Rhytmic Exam - Password Reset",
            recipients=[user.email],
            text_body=f"Use this link to reset your password: {reset_link}",
            html_body=f"<p>Use this link to reset your password:</p><p>{reset_link}</p>",
        )

    return MessageResponse(message="If the account exists, a reset email has been queued.")


@router.post("/auth/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordConfirm, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    user_id = verify_reset_password_token(payload.token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    return MessageResponse(message="Password updated successfully")
