from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    surname: Mapped[str] = mapped_column(String, nullable=False)
    sagf_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    answers: Mapped[list["ExamResult"]] = relationship("ExamResult", back_populates="linked_user")


class ExamResult(Base):
    __tablename__ = "exam_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sagf_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("users.sagf_id"), unique=True, index=True)
    theory_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    practical_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    practical_progress: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exam_start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    theory_taken: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    practical_taken: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exam_end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    linked_user: Mapped[Optional[User]] = relationship("User", back_populates="answers")


class ExamQuestion(Base):
    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(256), nullable=False)
    question_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    option_a: Mapped[str] = mapped_column(Text, nullable=False)
    option_b: Mapped[str] = mapped_column(Text, nullable=False)
    option_c: Mapped[str] = mapped_column(Text, nullable=False)
    option_d: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(String(1), nullable=False)
    exam_level: Mapped[str] = mapped_column(String(20), nullable=False)
    question_category: Mapped[str] = mapped_column(String(64), nullable=False)


class ExamPracticalAnswer(Base):
    __tablename__ = "exam_practical_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    discipline: Mapped[str] = mapped_column(String(64), nullable=False)
    internal_question_value: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    result_question_value: Mapped[str] = mapped_column(String(64), nullable=False)
    control_score: Mapped[str] = mapped_column(String(64), nullable=False)


__all__ = [
    "User",
    "ExamResult",
    "ExamQuestion",
    "ExamPracticalAnswer",
]