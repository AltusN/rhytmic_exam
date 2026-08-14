import pytest
from django.db import IntegrityError

from questions.models import Option, Question


@pytest.mark.django_db
def test_options_order_by_position():
    question = Question.objects.create(reference="Question 1")
    Option.objects.create(question=question, position=2, is_correct=False)
    Option.objects.create(question=question, position=1, is_correct=True)
    Option.objects.create(question=question, position=3, is_correct=False)
    Option.objects.create(question=question, position=4, is_correct=False)

    # ordering is already defined in the Option model's Meta class,
    # so we can just fetch all options and check their order
    options_ordered = list(Option.objects.all())
    assert options_ordered[0].position == 1
    assert options_ordered[1].position == 2
    assert options_ordered[2].position == 3
    assert options_ordered[3].position == 4


@pytest.mark.django_db
def test_duplicate_correct_option_for_the_same_question_is_refused():
    question = Question.objects.create(reference="Question 2")
    Option.objects.create(question=question, position=1, is_correct=True)

    with pytest.raises(IntegrityError):
        Option.objects.create(question=question, position=2, is_correct=True)


@pytest.mark.django_db
def test_two_questions_can_have_correct_options():
    question1 = Question.objects.create(reference="Question 3")
    question2 = Question.objects.create(reference="Question 4")

    Option.objects.create(question=question1, position=1, is_correct=True)
    Option.objects.create(question=question2, position=1, is_correct=True)

    assert Option.objects.filter(question=question1, is_correct=True).exists()
    assert Option.objects.filter(question=question2, is_correct=True).exists()

    assert Option.objects.count() == 2


@pytest.mark.django_db
def test_deleting_a_question_deletes_its_options():
    question = Question.objects.create(reference="Question 5")
    Option.objects.create(question=question, position=1, is_correct=True)
    Option.objects.create(question=question, position=2, is_correct=False)

    assert Option.objects.filter(question=question).count() == 2

    question.delete()

    assert Option.objects.count() == 0


@pytest.mark.django_db
def test_a_question_with_no_correct_option_still_saves():
    # This records a gap Task 7 closes with formset validation,
    # because "at least one correct option" can't be a row
    # constraint — the database has nothing to check until the
    # child rows exist.
    question = Question.objects.create(reference="Question 6")
    Option.objects.create(question=question, position=1, is_correct=False)
    Option.objects.create(question=question, position=2, is_correct=False)
    Option.objects.create(question=question, position=3, is_correct=False)
    Option.objects.create(question=question, position=4, is_correct=False)

    # Pylance may report `Question` has no attribute `options`, but this reverse
    # accessor is created dynamically by Django from Option.related_name.
    assert question.options.filter(is_correct=True).count() == 0  # type: ignore[attr-defined]


@pytest.mark.django_db
def test_duplicate_position_for_the_same_question_is_refused():
    question = Question.objects.create(reference="Question 7")
    Option.objects.create(question=question, position=1, is_correct=True)

    with pytest.raises(IntegrityError):
        Option.objects.create(question=question, position=1, is_correct=False)


@pytest.mark.django_db
def test_two_questions_can_have_options_with_the_same_position():
    question1 = Question.objects.create(reference="Question 8")
    question2 = Question.objects.create(reference="Question 9")

    Option.objects.create(question=question1, position=1, is_correct=True)
    Option.objects.create(question=question2, position=1, is_correct=False)

    assert Option.objects.filter(question=question1, position=1).exists()
    assert Option.objects.filter(question=question2, position=1).exists()
