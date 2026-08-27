import pytest
from django.apps import apps
from django.db import IntegrityError

from exams.models import Exam, ExamKind


def test_exams_app_exists():
    app = apps.get_app_config(
        "exams"
    )  # This will raise an error if the app is not properly configured

    assert app.models_module is not None


@pytest.mark.django_db
def test_two_exams_can_share_a_level_across_years():
    exam1 = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    exam2 = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2024,
    )

    assert Exam.objects.count() == 2
    assert exam1.year != exam2.year


@pytest.mark.django_db
def test_a_duplicate_level_year_kind_is_refused():
    Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )

    with pytest.raises(IntegrityError, match="uq_one_exam_per_level_year_kind"):
        Exam.objects.create(
            kind=ExamKind.PRACTICAL,
            level=1,
            year=2023,
        )


@pytest.mark.django_db
def test_kind_is_not_silently_theory():
    exam = Exam(
        level=1,
        year=2023,
    )
    with pytest.raises(IntegrityError, match="ck_exam_kind_is_valid"):
        exam.save()


@pytest.mark.django_db
def test_invalid_kind_is_refused():
    exam = Exam(
        kind="INVALID",
        level=1,
        year=2023,
    )
    with pytest.raises(IntegrityError, match="ck_exam_kind_is_valid"):
        exam.save()


@pytest.mark.django_db
def test_exams_are_ordered_newest_year_first():
    Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2024,
    )

    exams = list(Exam.objects.all())
    assert exams[0].year == 2024
    assert exams[1].year == 2023
