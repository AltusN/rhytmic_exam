import csv
import json
from datetime import datetime, timedelta
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_db
from ..db.models import ExamPracticalAnswer, ExamQuestion, ExamResult, User
from ..dependencies import get_admin_user, get_current_user
from ..exam_utils import calculate_practical_score, calculate_theory_score, make_question_for_exam
from ..schemas import ExamResultRead, PracticalProgressUpdate, PracticalSubmit, TheorySubmit

router = APIRouter(prefix="/exams", tags=["exams"])


async def _get_or_create_result(db: AsyncSession, sagf_id: str) -> ExamResult:
    result = await db.execute(select(ExamResult).where(ExamResult.sagf_id == sagf_id))
    exam_result = result.scalar_one_or_none()
    if exam_result is None:
        exam_result = ExamResult(sagf_id=sagf_id)
        db.add(exam_result)
        await db.flush()
    return exam_result


@router.get("/theory")
async def get_theory_exam(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.admin or current_user.level is None:
        stmt = select(ExamQuestion).where(ExamQuestion.question_category == "theory").order_by(ExamQuestion.question_id.asc())
    elif int(current_user.level) == 2:
        stmt = select(ExamQuestion).where(
            and_(
                ExamQuestion.question_category == "theory",
                ExamQuestion.exam_level.in_(["1", "2"]),
            )
        ).order_by(ExamQuestion.question_id.asc())
    else:
        stmt = select(ExamQuestion).where(
            and_(
                ExamQuestion.question_category == "theory",
                ExamQuestion.exam_level == str(current_user.level),
            )
        ).order_by(ExamQuestion.question_id.asc())

    result = await db.execute(stmt)
    questions = result.scalars().all()
    question_list = [make_question_for_exam(q) for q in questions]
    return {"questions": question_list}


@router.post("/theory/submit")
async def submit_theory_exam(
    payload: TheorySubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ExamResult).where(ExamResult.sagf_id == current_user.sagf_id))
    exam_result = result.scalar_one_or_none()
    if exam_result and exam_result.theory_taken and not current_user.admin:
        raise HTTPException(status_code=400, detail="Theory exam already completed")

    answers_stmt = select(ExamQuestion.question_id, ExamQuestion.answer).where(ExamQuestion.question_category == "theory")
    answers_data = (await db.execute(answers_stmt)).all()
    actual_answers = {str(qid): answer for qid, answer in answers_data}

    percentage, incorrect_answers = calculate_theory_score(payload.answers, actual_answers)

    if not current_user.admin:
        exam_result = await _get_or_create_result(db, current_user.sagf_id)
        exam_result.theory_answer = json.dumps(payload.answers)
        exam_result.theory_taken = True
        exam_result.exam_start_date = datetime.utcnow()
        await db.commit()

    return {
        "theory_percentage": percentage,
        "incorrect_answers": incorrect_answers,
    }


@router.get("/practical")
async def get_practical_exam(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(ExamResult).where(ExamResult.sagf_id == current_user.sagf_id))
    exam_result = result.scalar_one_or_none()

    if not current_user.admin and (exam_result is None or not exam_result.theory_taken):
        raise HTTPException(status_code=400, detail="Theory exam must be completed first")

    questions_stmt = select(ExamQuestion).where(ExamQuestion.question_category == "practical").order_by(ExamQuestion.question_id.asc())
    questions = (await db.execute(questions_stmt)).scalars().all()

    progress = {"q_id": 0, "v_id": 0, "answered": 0}
    if exam_result and exam_result.practical_progress:
        try:
            progress = json.loads(exam_result.practical_progress)
        except Exception:
            progress = {"q_id": 0, "v_id": 0, "answered": 0}

    q_dict = {"questions": [], "videos": [], "heading": []}
    for question in questions:
        q_payload = json.loads(question.question)
        q_dict["questions"].append(q_payload.get("question"))
        q_dict["heading"].append(q_payload.get("heading"))

        try:
            videos = json.loads(question.question_images or "{}").get("videos", [])
            if videos:
                q_dict["videos"] = videos
        except Exception:
            pass

    return {"q_dict": q_dict, "progress": progress}


@router.post("/practical/progress")
async def update_practical_progress(
    payload: PracticalProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    exam_result = await _get_or_create_result(db, current_user.sagf_id)
    progress = {
        "q_id": payload.q_id,
        "v_id": payload.v_id,
        "answered": payload.answered,
    }
    exam_result.practical_progress = json.dumps(progress)

    if payload.answer is not None:
        current_answers = {}
        if exam_result.practical_answer:
            try:
                current_answers = json.loads(exam_result.practical_answer)
            except Exception:
                current_answers = {}
        current_answers[f"answer_{payload.answered}"] = payload.answer
        exam_result.practical_answer = json.dumps(current_answers)

    await db.commit()
    return {"message": "Progress saved", "progress": progress}


@router.post("/practical/submit")
async def submit_practical_exam(
    payload: PracticalSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    answers_stmt = select(ExamPracticalAnswer).order_by(ExamPracticalAnswer.id.asc())
    answer_rows = (await db.execute(answers_stmt)).scalars().all()

    percentage, practical_breakdown = calculate_practical_score(payload.answers, answer_rows)

    if not current_user.admin:
        exam_result = await _get_or_create_result(db, current_user.sagf_id)
        exam_result.practical_answer = json.dumps(payload.answers)
        exam_result.practical_taken = True
        exam_result.exam_end_date = datetime.utcnow()
        await db.commit()

    return {
        "practical_percentage": percentage,
        "practical_breakdown": practical_breakdown,
    }


@router.get("/results", response_model=ExamResultRead)
async def get_my_results(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExamResultRead:
    result = await db.execute(select(ExamResult).where(ExamResult.sagf_id == current_user.sagf_id))
    exam_result = result.scalar_one_or_none()
    if exam_result is None:
        raise HTTPException(status_code=404, detail="No exam result found")

    theory_percentage = None
    practical_percentage = None
    practical_breakdown = None

    if exam_result.theory_answer:
        theory_answers = json.loads(exam_result.theory_answer)
        actual_answers_rows = (
            await db.execute(select(ExamQuestion.question_id, ExamQuestion.answer).where(ExamQuestion.question_category == "theory"))
        ).all()
        actual_answers = {str(qid): ans for qid, ans in actual_answers_rows}
        theory_percentage, _ = calculate_theory_score(theory_answers, actual_answers)

    if exam_result.practical_answer:
        practical_answers = json.loads(exam_result.practical_answer)
        practical_rows = (await db.execute(select(ExamPracticalAnswer))).scalars().all()
        practical_percentage, practical_breakdown = calculate_practical_score(practical_answers, practical_rows)

    return ExamResultRead(
        sagf_id=exam_result.sagf_id,
        theory_taken=exam_result.theory_taken,
        practical_taken=exam_result.practical_taken,
        exam_start_date=exam_result.exam_start_date,
        exam_end_date=exam_result.exam_end_date,
        theory_percentage=theory_percentage,
        practical_percentage=practical_percentage,
        practical_breakdown=practical_breakdown,
    )


@router.get("/admin/results", dependencies=[Depends(get_admin_user)], tags=["admin"])
async def admin_results(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=8, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> dict:
    offset = (page - 1) * per_page

    total = (await db.execute(select(func.count()).select_from(ExamResult))).scalar_one()
    rows = (
        await db.execute(
            select(ExamResult).order_by(ExamResult.exam_start_date.desc()).offset(offset).limit(per_page)
        )
    ).scalars().all()

    data = []
    now = datetime.utcnow()

    practical_rows = (await db.execute(select(ExamPracticalAnswer))).scalars().all()
    theory_rows = (await db.execute(select(ExamQuestion.question_id, ExamQuestion.answer).where(ExamQuestion.question_category == "theory"))).all()
    theory_actual = {str(qid): ans for qid, ans in theory_rows}

    for row in rows:
        theory_pct = None
        practical_pct = None

        if row.theory_answer:
            theory_answers = json.loads(row.theory_answer)
            theory_pct, _ = calculate_theory_score(theory_answers, theory_actual)

        if row.practical_answer:
            practical_answers = json.loads(row.practical_answer)
            practical_pct, _ = calculate_practical_score(practical_answers, practical_rows)

        recent = row.exam_end_date is not None and (now - row.exam_end_date) <= timedelta(days=2)

        data.append(
            {
                "sagf_id": row.sagf_id,
                "theory_percentage": theory_pct,
                "practical_percentage": practical_pct,
                "recent": recent,
                "theory_taken": row.theory_taken,
                "practical_taken": row.practical_taken,
                "exam_start_date": row.exam_start_date,
                "exam_end_date": row.exam_end_date,
            }
        )

    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": data,
    }


@router.get("/admin/results/export", dependencies=[Depends(get_admin_user)], tags=["admin"])
async def export_results_csv(db: AsyncSession = Depends(get_db)) -> Response:
    rows = (await db.execute(select(ExamResult).order_by(ExamResult.exam_start_date.asc()))).scalars().all()
    practical_rows = (await db.execute(select(ExamPracticalAnswer))).scalars().all()
    theory_rows = (await db.execute(select(ExamQuestion.question_id, ExamQuestion.answer).where(ExamQuestion.question_category == "theory"))).all()
    theory_actual = {str(qid): ans for qid, ans in theory_rows}

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["sagf_id", "theory_percentage", "practical_percentage", "theory_taken", "practical_taken", "exam_start_date", "exam_end_date"])

    for row in rows:
        theory_pct = None
        practical_pct = None

        if row.theory_answer:
            theory_answers = json.loads(row.theory_answer)
            theory_pct, _ = calculate_theory_score(theory_answers, theory_actual)

        if row.practical_answer:
            practical_answers = json.loads(row.practical_answer)
            practical_pct, _ = calculate_practical_score(practical_answers, practical_rows)

        writer.writerow(
            [
                row.sagf_id,
                theory_pct,
                practical_pct,
                row.theory_taken,
                row.practical_taken,
                row.exam_start_date,
                row.exam_end_date,
            ]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=exam_results.csv"},
    )
