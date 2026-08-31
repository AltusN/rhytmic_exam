import pytest
from django.db import IntegrityError
from django.db.models import ProtectedError

from exams.models import ComponentQuestion, Exam, ExamComponent, ExamKind, MarkingScheme
from questions.models import Question


def _theory_exam_and_component(*, level: int) -> ExamComponent:
    exam = Exam.objects.create(kind=ExamKind.THEORY, level=level, year=2026)
    return ExamComponent.objects.create(
        exam=exam,
        name="Theory Component",
        position=1,
        marking_scheme=MarkingScheme.CHOICE,
        aspect="",
        difference_steps=[],
    )


@pytest.mark.django_db
def test_a_level_two_component_contains_level_ones_questions_too():
    component_1 = _theory_exam_and_component(level=1)
    component_2 = _theory_exam_and_component(level=2)

    questions = [Question.objects.create(reference=f"Q{i}") for i in range(1, 4)]
    extra_questions = [Question.objects.create(reference=f"Q{i}") for i in range(4, 6)]

    for position, question in enumerate(questions, start=1):
        ComponentQuestion.objects.create(
            component=component_1, question=question, position=position
        )
    for position, question in enumerate([*questions, *extra_questions], start=1):
        ComponentQuestion.objects.create(
            component=component_2, question=question, position=position
        )

    level_1_pks = {m.question_id for m in component_1.question_members.all()}
    level_2_pks = {m.question_id for m in component_2.question_members.all()}

    # A count alone would pass against a schema that copied questions per
    # level. The proper-subset check is what forces sharing, not duplication.
    assert level_1_pks < level_2_pks
    assert len(level_2_pks) == 5


@pytest.mark.django_db
def test_correcting_a_question_reaches_every_component_referencing_it():
    component_1 = _theory_exam_and_component(level=1)
    component_2 = _theory_exam_and_component(level=2)
    question = Question.objects.create(reference="ORIGINAL")

    ComponentQuestion.objects.create(
        component=component_1, question=question, position=1
    )
    ComponentQuestion.objects.create(
        component=component_2, question=question, position=1
    )

    question.reference = "CORRECTED"
    question.save()

    seen_by_1 = component_1.question_members.get().question
    seen_by_2 = component_2.question_members.get().question

    assert seen_by_1.reference == "CORRECTED"
    assert seen_by_2.reference == "CORRECTED"


@pytest.mark.django_db
def test_the_same_question_twice_in_one_component_is_refused():
    component = _theory_exam_and_component(level=1)
    question = Question.objects.create(reference="Q1")

    ComponentQuestion.objects.create(component=component, question=question, position=1)

    with pytest.raises(IntegrityError, match="uq_one_question_per_component"):
        ComponentQuestion.objects.create(
            component=component, question=question, position=2
        )


@pytest.mark.django_db
def test_a_question_referenced_by_a_component_cannot_be_deleted():
    component = _theory_exam_and_component(level=1)
    question = Question.objects.create(reference="Q1")
    ComponentQuestion.objects.create(component=component, question=question, position=1)

    with pytest.raises(ProtectedError):
        question.delete()


@pytest.mark.django_db
def test_members_come_back_in_position_order():
    component = _theory_exam_and_component(level=1)
    question_1 = Question.objects.create(reference="Q1")
    question_2 = Question.objects.create(reference="Q2")

    # Created out of order so the test only passes if ordering sorts them.
    ComponentQuestion.objects.create(
        component=component, question=question_2, position=2
    )
    ComponentQuestion.objects.create(
        component=component, question=question_1, position=1
    )

    members = list(component.question_members.all())

    assert [m.position for m in members] == [1, 2]
    assert [m.question_id for m in members] == [question_1.pk, question_2.pk]
