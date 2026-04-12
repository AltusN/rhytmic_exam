from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    name: str
    surname: str
    sagf_id: str
    email: str
    level: int | None = None
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    level: int | None = None
    name: str
    surname: str
    sagf_id: str
    email: str
    enabled: bool
    admin: bool

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    name: str | None = None
    surname: str | None = None
    email: str | None = None


class AdminUserUpdate(UserUpdate):
    enabled: bool | None = None
    admin: bool | None = None
    level: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class MessageResponse(BaseModel):
    message: str


class ResetPasswordRequest(BaseModel):
    email: str


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str


class ExamQuestionCreate(BaseModel):
    question: str
    question_type: str
    question_images: str | None = None
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str
    exam_level: str
    question_category: str
    question_id: int | None = None


class ExamQuestionUpdate(BaseModel):
    question: str | None = None
    question_type: str | None = None
    question_images: str | None = None
    option_a: str | None = None
    option_b: str | None = None
    option_c: str | None = None
    option_d: str | None = None
    answer: str | None = None
    exam_level: str | None = None
    question_category: str | None = None


class ExamQuestionRead(BaseModel):
    id: int
    question_id: int
    question: str
    question_type: str
    question_images: str | None
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    answer: str
    exam_level: str
    question_category: str

    model_config = ConfigDict(from_attributes=True)


class TheorySubmit(BaseModel):
    answers: dict[str, str]


class PracticalSubmit(BaseModel):
    answers: dict[str, str]


class PracticalProgressUpdate(BaseModel):
    q_id: int
    v_id: int
    answered: int
    answer: str | None = None


class ExamResultRead(BaseModel):
    sagf_id: str | None
    theory_taken: bool
    practical_taken: bool
    exam_start_date: datetime | None = None
    exam_end_date: datetime | None = None
    theory_percentage: float | None = None
    practical_percentage: float | None = None
    practical_breakdown: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)