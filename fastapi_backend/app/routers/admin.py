from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import ExamQuestion, User
from ..dependencies import get_admin_user, get_current_user
from ..email import send_email
from ..schemas import AdminUserUpdate, ExamQuestionCreate, ExamQuestionRead, ExamQuestionUpdate, UserRead

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_admin_user)])


@router.get("/users")
async def list_users(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=8, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    offset = (page - 1) * per_page

    total = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    rows = (await db.execute(select(User).order_by(User.id.asc()).offset(offset).limit(per_page))).scalars().all()

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [UserRead.model_validate(u) for u in rows],
    }


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    was_enabled = user.enabled

    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.surname is not None:
        user.surname = payload.surname.strip()
    if payload.email is not None:
        user.email = payload.email.strip().lower()
    if payload.enabled is not None:
        user.enabled = payload.enabled
    if payload.admin is not None:
        user.admin = payload.admin
    if payload.level is not None:
        user.level = payload.level

    await db.commit()
    await db.refresh(user)

    if not was_enabled and user.enabled:
        send_email(
            subject="Rhytmic Exam - User Registration Confirmed",
            recipients=[user.email],
            text_body=f"Hi {user.name}, your account is now enabled.",
            html_body=f"<p>Hi {user.name}, your account is now enabled.</p>",
        )

    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_admin: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted"}


@router.get("/questions")
async def list_questions(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=8, ge=1, le=100),
    level: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    offset = (page - 1) * per_page

    stmt = select(ExamQuestion)
    count_stmt = select(func.count()).select_from(ExamQuestion)

    if level:
        stmt = stmt.where(ExamQuestion.exam_level == level)
        count_stmt = count_stmt.where(ExamQuestion.exam_level == level)
    if category:
        stmt = stmt.where(ExamQuestion.question_category == category)
        count_stmt = count_stmt.where(ExamQuestion.question_category == category)

    total = (await db.execute(count_stmt)).scalar_one()
    rows = (
        await db.execute(stmt.order_by(ExamQuestion.question_id.asc()).offset(offset).limit(per_page))
    ).scalars().all()

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": [ExamQuestionRead.model_validate(q) for q in rows],
    }


@router.get("/questions/{question_id}", response_model=ExamQuestionRead)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)) -> ExamQuestionRead:
    result = await db.execute(select(ExamQuestion).where(ExamQuestion.question_id == question_id))
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return question


@router.post("/questions", response_model=ExamQuestionRead)
async def create_question(payload: ExamQuestionCreate, db: AsyncSession = Depends(get_db)) -> ExamQuestionRead:
    question_id = payload.question_id
    if question_id is None:
        max_qid = (await db.execute(select(func.max(ExamQuestion.question_id)))).scalar_one_or_none() or 0
        question_id = max_qid + 1

    question = ExamQuestion(
        question_id=question_id,
        question=payload.question,
        question_type=payload.question_type,
        question_images=payload.question_images,
        option_a=payload.option_a,
        option_b=payload.option_b,
        option_c=payload.option_c,
        option_d=payload.option_d,
        answer=payload.answer,
        exam_level=payload.exam_level,
        question_category=payload.question_category,
    )

    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.patch("/questions/{question_id}", response_model=ExamQuestionRead)
async def update_question(
    question_id: int,
    payload: ExamQuestionUpdate,
    db: AsyncSession = Depends(get_db),
) -> ExamQuestionRead:
    result = await db.execute(select(ExamQuestion).where(ExamQuestion.question_id == question_id))
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(question, field, value)

    await db.commit()
    await db.refresh(question)
    return question


@router.delete("/questions/{question_id}")
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(ExamQuestion).where(ExamQuestion.question_id == question_id))
    question = result.scalar_one_or_none()
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    await db.delete(question)
    await db.commit()
    return {"message": "Question deleted"}
