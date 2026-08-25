from decimal import Decimal

import pytest

from questions.models import (
    Apparatus,
    Kind,
    Option,
    PracticalItem,
    Question,
    QuestionBlock,
    Routine,
)


@pytest.fixture
def practical_item(db):
    apparatus = Apparatus.objects.create(name="Ball", position=1)
    routine = Routine.objects.create(
        apparatus=apparatus, label="2006 senior ball, candidate A"
    )
    return PracticalItem.objects.create(
        routine=routine, aspect="DA", expert_score=Decimal("4.20")
    )


@pytest.mark.django_db
def test_editing_an_expert_score_records_both_values(practical_item):

    practical_item.expert_score = Decimal("4.50")
    practical_item.save()

    assert practical_item.history.count() == 2
    # Ordering puts newest first, so the last record is the original value
    assert practical_item.history.last().expert_score == Decimal("4.20")


@pytest.mark.django_db
def test_history_records_the_change_type(practical_item):

    practical_item.expert_score = Decimal("4.50")
    practical_item.save()

    assert practical_item.history.first().history_type == "~"  # ~ indicates a change
    assert practical_item.history.last().history_type == "+"  # + indicates creation


def test_apparatus_has_no_history():
    assert hasattr(Apparatus, "history") is False


@pytest.mark.django_db
def test_rewording_a_block_records_both_versions():
    question = Question.objects.create(reference="ref1")
    original_text = "Awesome question block"
    question_block = QuestionBlock.objects.create(
        question=question, position=1, kind=Kind.TEXT, text=original_text
    )

    question_block.text = "Not nearly as awesome question block"
    question_block.save()

    assert question_block.history.count() == 2
    assert question_block.history.last().text == original_text


@pytest.mark.django_db
def test_block_history_survives_deleting_the_question():
    question = Question.objects.create(reference="ref1")
    question_block = QuestionBlock.objects.create(
        question=question, position=1, kind=Kind.TEXT, text="Test block"
    )
    block_pk = question_block.pk

    question.delete()

    # The live block is gone after cascade delete
    assert QuestionBlock.objects.filter(pk=block_pk).exists() is False

    # But the historical records remain
    HistoricalQuestionBlock = QuestionBlock.history.model
    historical_records = HistoricalQuestionBlock.objects.filter(id=block_pk)
    assert historical_records.count() == 2
    # First record is creation (+), second is deletion (-)
    # Ordering puts newest first, so the last record is the creation
    assert historical_records.last().history_type == "+"
    assert historical_records.first().history_type == "-"


@pytest.mark.django_db
def test_correcting_a_reference_records_both_versions():
    question = Question.objects.create(reference="ref1")
    original_reference = question.reference

    question.reference = "ref2"
    question.save()

    assert question.history.count() == 2
    assert question.history.last().reference == original_reference


@pytest.mark.django_db
def test_flipping_the_correct_option_records_both_versions():
    question = Question.objects.create(reference="ref 1")
    # A single option avoids uq_one_correct_option_per_question when flipping.
    option = Option.objects.create(question=question, position=1, is_correct=False)

    option.is_correct = True
    option.save()

    assert option.history.count() == 2
    assert option.history.last().is_correct is False


@pytest.mark.django_db
def test_rewording_an_option_block_records_both_versions():
    question = Question.objects.create(reference="ref 1")
    option = Option.objects.create(question=question, position=1, is_correct=False)
    original_text = "Awesome option block"
    option_block = option.blocks.create(position=1, kind=Kind.TEXT, text=original_text)

    option_block.text = "Not nearly as awesome option block"
    option_block.save()

    assert option_block.history.count() == 2
    assert option_block.history.last().text == original_text
