from datetime import UTC, datetime

import pytest
from django.db.models import ProtectedError

from exams.models import Exam, ExamKind, Sitting, Status


@pytest.mark.django_db
def test_a_judge_accumulates_sittings_over_years(django_user_model):
    judge = django_user_model.objects.create(username="judge_judy", password="x")
    exam1 = Exam.objects.create(level=1, year=2026, kind=ExamKind.THEORY)
    exam2 = Exam.objects.create(level=1, year=2030, kind=ExamKind.THEORY)

    Sitting.objects.create(
        judge=judge,
        exam=exam1,
    )
    Sitting.objects.create(
        judge=judge,
        exam=exam2,
    )

    assert {s.exam.year for s in judge.sittings.all()} == {2026, 2030}


@pytest.mark.django_db
def test_a_judge_can_retake_the_same_exam_after_failing(django_user_model):
    judge = django_user_model.objects.create(username="judge_judy", password="x")
    exam = Exam.objects.create(level=1, year=2026, kind=ExamKind.THEORY)

    Sitting.objects.create(
        judge=judge,
        exam=exam,
    )
    Sitting.objects.create(
        judge=judge,
        exam=exam,
    )

    assert Sitting.objects.filter(judge=judge, exam=exam).count() == 2


@pytest.mark.django_db
def test_a_new_sitting_is_pending(django_user_model):
    judge = django_user_model.objects.create(username="judge_judy", password="x")
    exam = Exam.objects.create(level=1, year=2026, kind=ExamKind.THEORY)

    sitting = Sitting.objects.create(
        judge=judge,
        exam=exam,
    )
    sitting.refresh_from_db()

    assert sitting.status == Status.PENDING


@pytest.mark.django_db
def test_a_judge_with_no_practical_sitting_has_no_practical_result(django_user_model):
    judge = django_user_model.objects.create(username="judge_judy", password="x")
    exam = Exam.objects.create(level=1, year=2026, kind=ExamKind.THEORY)

    Sitting.objects.create(
        judge=judge,
        exam=exam,
    )

    assert Sitting.objects.filter(judge=judge, exam__kind=ExamKind.THEORY).exists()
    assert (
        Sitting.objects.filter(judge=judge, exam__kind=ExamKind.PRACTICAL).exists()
        is False
    )


@pytest.mark.django_db
def test_a_judge_with_sittings_cannot_be_deleted(django_user_model):
    judge = django_user_model.objects.create(username="judge_judy", password="x")
    exam = Exam.objects.create(level=1, year=2026, kind=ExamKind.THEORY)

    Sitting.objects.create(
        judge=judge,
        exam=exam,
    )

    with pytest.raises(ProtectedError):
        judge.delete()


@pytest.mark.django_db
def test_certifying_records_who_and_when(django_user_model):
    judge = django_user_model.objects.create(username="judge_judy", password="x")
    official = django_user_model.objects.create(username="official", password="x")
    exam = Exam.objects.create(level=1, year=2026, kind=ExamKind.THEORY)
    sitting = Sitting.objects.create(judge=judge, exam=exam)  # PENDING, uncertified

    sitting.status = Status.CERTIFIED
    sitting.certified_by = official
    cert_date = datetime.now(UTC)
    sitting.certified_at = cert_date
    sitting.save()

    sitting.refresh_from_db()
    assert sitting.certified_by == official
    assert sitting.certified_at == cert_date

    assert sitting.history.count() == 2
    earliest = sitting.history.last()
    assert earliest.certified_by is None
    assert earliest.certified_at is None
