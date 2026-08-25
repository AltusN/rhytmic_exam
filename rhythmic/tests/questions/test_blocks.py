import pytest
from django.db import IntegrityError, connection

from questions.models import (
    ContentBlock,
    Kind,
    Option,
    OptionBlock,
    Question,
    QuestionBlock,
)


@pytest.fixture
def immediate_constraints(db):
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")


@pytest.mark.django_db
def test_a_stem_is_an_ordered_list_of_blocks():
    question = Question.objects.create(reference="ref1")
    question_block_third = QuestionBlock.objects.create(
        question=question, position=3, kind=Kind.TEXT, text="Third block"
    )
    question_block_first = QuestionBlock.objects.create(
        question=question, position=1, kind=Kind.TEXT, text="First block"
    )
    question_block_second = QuestionBlock.objects.create(
        question=question, position=2, kind=Kind.TEXT, text="Second block"
    )

    assert list(question.blocks.all()) == [
        question_block_first,
        question_block_second,
        question_block_third,
    ]


@pytest.mark.django_db
def test_an_option_carries_its_own_blocks():
    question = Question.objects.create(reference="ref2")
    option = Option.objects.create(question=question, position=1, is_correct=False)
    option_block_3 = OptionBlock.objects.create(
        option=option, position=3, kind=Kind.TEXT, text="Option block 3"
    )
    option_block_2 = OptionBlock.objects.create(
        option=option, position=2, kind=Kind.TEXT, text="Option block 2"
    )
    option_block_1 = OptionBlock.objects.create(
        option=option, position=1, kind=Kind.TEXT, text="Option block 1"
    )
    option_2 = Option.objects.create(question=question, position=2, is_correct=False)
    option_2_block = OptionBlock.objects.create(
        option=option_2, position=1, kind=Kind.TEXT, text="Option 2 block"
    )

    assert list(option.blocks.all()) == [
        option_block_1,
        option_block_2,
        option_block_3,
    ]
    assert list(option_2.blocks.all()) == [option_2_block]


@pytest.mark.django_db
def test_deleting_a_question_deletes_its_blocks():
    question = Question.objects.create(reference="ref3")
    question_block = QuestionBlock.objects.create(
        question=question, position=1, kind=Kind.TEXT, text="A block"
    )
    option = Option.objects.create(question=question, position=1, is_correct=False)
    option_block = OptionBlock.objects.create(
        option=option, position=1, kind=Kind.TEXT, text="An option block"
    )

    assert QuestionBlock.objects.filter(id=question_block.id).exists()
    assert OptionBlock.objects.filter(id=option_block.id).exists()

    question.delete()

    assert not QuestionBlock.objects.filter(id=question_block.id).exists()
    assert not OptionBlock.objects.filter(id=option_block.id).exists()


@pytest.mark.django_db
def test_contentblock_has_no_table_of_its_own():
    assert ContentBlock._meta.abstract is True


@pytest.mark.django_db
def test_a_text_block_without_text_is_refused():
    question = Question.objects.create(reference="text block not text")

    with pytest.raises(
        IntegrityError, match=r"questions_questionblock_kind_matches_payload"
    ):
        QuestionBlock.objects.create(question=question, position=1, kind=Kind.TEXT)


@pytest.mark.django_db
def test_an_image_block_carrying_text_is_refused():
    question = Question.objects.create(reference="image test")

    with pytest.raises(
        IntegrityError, match=r"questions_questionblock_kind_matches_payload"
    ):
        QuestionBlock.objects.create(
            question=question,
            position=1,
            kind=Kind.IMAGE,
            image="/test/image.jpg",
            text="I shouldn't be here",
        )


@pytest.mark.django_db
def test_the_kind_constraint_applies_to_the_option_block_too():
    question = Question.objects.create(reference="option block test")
    option = Option.objects.create(question=question, position=1, is_correct=False)

    with pytest.raises(
        IntegrityError, match=r"questions_optionblock_kind_matches_payload"
    ):
        OptionBlock.objects.create(option=option, position=1, kind=Kind.TEXT)


@pytest.mark.django_db
def test_two_blocks_cannot_have_the_same_position(immediate_constraints):
    question = Question.objects.create(reference="duplicate position test")
    QuestionBlock.objects.create(
        question=question, position=1, kind=Kind.TEXT, text="First block"
    )

    with pytest.raises(IntegrityError, match=r"uq_unique_block_position_per_question"):
        QuestionBlock.objects.create(
            question=question, position=1, kind=Kind.TEXT, text="Duplicate block"
        )


@pytest.mark.django_db
def test_two_questions_may_have_blocks_with_the_same_position(immediate_constraints):
    question1 = Question.objects.create(reference="question 1")
    question2 = Question.objects.create(reference="question 2")

    block1 = QuestionBlock.objects.create(
        question=question1, position=1, kind=Kind.TEXT, text="Block for question 1"
    )
    block2 = QuestionBlock.objects.create(
        question=question2, position=1, kind=Kind.TEXT, text="Block for question 2"
    )

    assert list(question1.blocks.all()) == [block1]
    assert list(question2.blocks.all()) == [block2]


@pytest.mark.django_db
def test_a_type_one_question_is_text_stem_and_text_options():
    question = Question.objects.create(reference="ref 2005")
    stem_block = QuestionBlock.objects.create(
        question=question, position=1, kind=Kind.TEXT, text="This is the stem"
    )
    options = []
    for position in [4, 3, 2, 1]:
        option = Option.objects.create(
            question=question,
            position=position,
            is_correct=position == 4,
        )
        OptionBlock.objects.create(
            option=option,
            position=1,
            kind=Kind.TEXT,
            text=f"This is option {position}",
        )
        options.append(option)

    assert list(question.blocks.all()) == [stem_block]
    assert list(question.options.all()) == sorted(options, key=lambda o: o.position)
    assert [
        [block.text for block in option.blocks.all()]
        for option in question.options.all()
    ] == [
        ["This is option 1"],
        ["This is option 2"],
        ["This is option 3"],
        ["This is option 4"],
    ]


def test_str_reports_video_filename():
    question = Question(reference="ref-video")
    block = QuestionBlock(
        question=question, position=1, kind=Kind.VIDEO, video="blocks/clip.mp4"
    )
    assert str(block) == "Video Block at position 1: clip.mp4"


def test_str_reports_image_filename():
    question = Question(reference="ref-image")
    block = QuestionBlock(
        question=question, position=1, kind=Kind.IMAGE, image="blocks/picture.png"
    )
    assert str(block) == "Image Block at position 1: picture.png"


def test_str_on_an_unsaved_block_with_no_kind():
    question = Question(reference="ref-unsaved")
    block = QuestionBlock(question=question, position=1)
    assert str(block) == "New block (unsaved)"


def test_str_reports_truncated_text_for_long_text_blocks():
    question = Question(reference="ref-long-text")
    long_text = "This is a very long text block that should be truncated in the string representation."
    block = QuestionBlock(question=question, position=1, kind=Kind.TEXT, text=long_text)
    # Django's Truncator.chars(40) keeps 40 total characters, ending in a single "…".
    assert (
        str(block)
        == "Text Block at position 1: This is a very long text block that sho…"
    )
