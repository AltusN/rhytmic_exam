import pytest
from django.apps import apps
from django.db import IntegrityError

from exams.models import Exam, ExamComponent, ExamKind, MarkingScheme


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


@pytest.mark.django_db
def test_a_theory_exam_has_one_component():
    exam = Exam.objects.create(
        kind=ExamKind.THEORY,
        level=1,
        year=2023,
    )
    ExamComponent.objects.create(
        exam=exam,
        name="Theory Component",
        position=1,
        marking_scheme=MarkingScheme.CHOICE,
        aspect="",
    )

    exam.refresh_from_db()
    component = exam.components.get()

    assert exam.components.count() == 1
    assert component.marking_scheme == MarkingScheme.CHOICE
    assert component.aspect == ""


@pytest.mark.django_db
def test_a_practical_exam_has_four_components_per_aspect():
    exam = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    for position, aspect in enumerate(["DA", "DB", "AV", "EX"], start=1):
        ExamComponent.objects.create(
            exam=exam,
            name=f"Practical Component {aspect}-{position}",
            position=position,
            marking_scheme=MarkingScheme.NUMERIC,
            aspect=aspect,
        )

    assert exam.components.count() == 4


@pytest.mark.django_db
def test_a_second_component_for_the_same_aspect_is_refused():
    exam = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    ExamComponent.objects.create(
        exam=exam,
        name="Practical Component DA-1",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
    )

    with pytest.raises(IntegrityError, match="uq_one_component_per_aspect_per_exam"):
        ExamComponent.objects.create(
            exam=exam,
            name="Practical Component DA-2",
            position=2,
            marking_scheme=MarkingScheme.NUMERIC,
            aspect="DA",
        )


@pytest.mark.django_db
def test_a_second_component_for_the_same_position_is_refused():
    exam = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    ExamComponent.objects.create(
        exam=exam,
        name="Practical Component DA-1",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
    )

    with pytest.raises(IntegrityError, match="uq_one_component_position_per_exam"):
        ExamComponent.objects.create(
            exam=exam,
            name="Practical Component DB-1",
            position=1,
            marking_scheme=MarkingScheme.NUMERIC,
            aspect="DB",
        )


@pytest.mark.django_db
def test_marking_scheme_is_not_silently_choice():
    exam = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    with pytest.raises(IntegrityError, match="ck_component_marking_scheme_is_valid"):
        ExamComponent.objects.create(
            exam=exam,
            name="Practical Component DA-1",
            position=1,
            aspect="DA",
        )


@pytest.mark.django_db
def test_deleting_an_exam_cascades_to_components():
    exam = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    component = ExamComponent.objects.create(
        exam=exam,
        name="Practical Component DA-1",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
    )

    exam.delete()
    assert ExamComponent.objects.filter(id=component.id).count() == 0


@pytest.mark.django_db
def test_components_are_ordered_by_position():
    exam = Exam.objects.create(
        kind=ExamKind.PRACTICAL,
        level=1,
        year=2023,
    )
    component1 = ExamComponent.objects.create(
        exam=exam,
        name="Practical Component DA-1",
        position=2,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DA",
    )
    component2 = ExamComponent.objects.create(
        exam=exam,
        name="Practical Component DB-1",
        position=1,
        marking_scheme=MarkingScheme.NUMERIC,
        aspect="DB",
    )

    components = list(ExamComponent.objects.all())
    assert components == [component2, component1]
