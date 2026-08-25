from decimal import Decimal

import pytest
from django.apps import apps
from django.db import IntegrityError
from django.db.models import ProtectedError

from questions.models import Apparatus, Aspect, PracticalItem, Routine


def test_questions_app_is_installed():
    # Check if the 'questions' app is installed
    assert apps.is_installed("questions"), (
        "The 'questions' app is not installed in the Django project."
    )


@pytest.mark.django_db
def test_apparatus_orders_by_position():
    # create Appratus instances out of order
    Apparatus.objects.create(name="Apparatus B", position=2)
    Apparatus.objects.create(name="Apparatus A", position=1)
    Apparatus.objects.create(name="Apparatus C", position=3)

    # fetch apparatus ordered by position
    apparatus_ordered = list(Apparatus.objects.all())
    assert apparatus_ordered[0].name == "Apparatus A"
    assert apparatus_ordered[1].name == "Apparatus B"
    assert apparatus_ordered[2].name == "Apparatus C"


@pytest.mark.django_db
def test_apparatus_name_is_unique():
    Apparatus.objects.create(name="Apparatus A", position=1)

    with pytest.raises(IntegrityError):
        Apparatus.objects.create(name="Apparatus A", position=2)


@pytest.mark.django_db
def test_routine_belongs_to_apparatus():
    apparatus = Apparatus.objects.create(name="Apparatus A", position=1)
    routine = Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video.mp4"
    )

    assert routine.apparatus == apparatus
    assert routine.label == "Routine 1"
    assert routine.video.name == "path/to/video.mp4"


@pytest.mark.django_db
def test_deleting_an_appartus_in_use_is_refused():
    apparatus = Apparatus.objects.create(name="Apparatus A", position=1)
    Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video.mp4"
    )

    with pytest.raises(ProtectedError):
        apparatus.delete()


@pytest.mark.django_db
def test_a_routine_has_one_item_per_aspect():
    apparatus = Apparatus.objects.create(name="Apparatus A", position=1)
    routine = Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video.mp4"
    )
    PracticalItem.objects.create(
        routine=routine, aspect=Aspect.DA, expert_score=Decimal("9.5")
    )
    PracticalItem.objects.create(
        routine=routine, aspect=Aspect.DB, expert_score=Decimal("8.0")
    )
    PracticalItem.objects.create(
        routine=routine, aspect=Aspect.AV, expert_score=Decimal("7.5")
    )
    PracticalItem.objects.create(
        routine=routine, aspect=Aspect.EX, expert_score=Decimal("9.0")
    )

    # Pylance may report `Routine` has no attribute `items`, but this reverse
    # accessor is created dynamically by Django from PracticalItem.related_name.
    assert routine.items.count() == 4  # type: ignore[attr-defined]


@pytest.mark.django_db
def test_duplicate_aspect_for_a_routine_is_rejected():
    apparatus = Apparatus.objects.create(name="Apparatus A", position=1)
    routine = Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video.mp4"
    )
    PracticalItem.objects.create(
        routine=routine, aspect=Aspect.DA, expert_score=Decimal("9.5")
    )

    with pytest.raises(IntegrityError):
        PracticalItem.objects.create(
            routine=routine, aspect=Aspect.DA, expert_score=Decimal("8.0")
        )


@pytest.mark.django_db
def test_expert_score_is_stored_as_decimal():
    apparatus = Apparatus.objects.create(name="Apparatus A", position=1)
    routine = Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video.mp4"
    )
    item = PracticalItem.objects.create(
        routine=routine, aspect=Aspect.DA, expert_score=Decimal("4.20")
    )
    item_from_db = PracticalItem.objects.get(pk=item.pk)

    assert isinstance(item_from_db.expert_score, Decimal)
    assert item_from_db.expert_score == Decimal("4.20")


@pytest.mark.django_db
def test_the_same_aspect_on_two_routines_is_ok():
    apparatus = Apparatus.objects.create(name="Apparatus A", position=1)
    routine1 = Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video1.mp4"
    )
    routine2 = Routine.objects.create(
        apparatus=apparatus, label="Routine 2", video="path/to/video2.mp4"
    )

    item1 = PracticalItem.objects.create(
        routine=routine1, aspect=Aspect.DA, expert_score=Decimal("9.5")
    )
    item2 = PracticalItem.objects.create(
        routine=routine2, aspect=Aspect.DA, expert_score=Decimal("8.0")
    )

    assert item1.aspect == item2.aspect
    assert item1.routine != item2.routine


@pytest.mark.django_db
def test_practical_item_str_representation():
    apparatus = Apparatus.objects.create(name="Rope", position=1)
    routine = Routine.objects.create(
        apparatus=apparatus, label="Routine 1", video="path/to/video.mp4"
    )
    practical_item = PracticalItem.objects.create(
        routine=routine, aspect=Aspect.DA, expert_score=Decimal("5.00")
    )

    assert str(practical_item) == "Rope - Routine 1 - DA - 5.00"


@pytest.mark.django_db
def test_routine_ordering_by_apparatus_and_label():
    # positions run against creation order, so the ordering can only be
    # coming from apparatus__position, not from pk/creation order.
    apparatus1 = Apparatus.objects.create(name="Apparatus A", position=2)
    apparatus2 = Apparatus.objects.create(name="Apparatus B", position=1)

    # Created against label order (2 before 1), so dropping label falls back
    # to creation/pk order and disagrees with the expected label-sorted result.
    routine2 = Routine.objects.create(
        apparatus=apparatus1, label="Routine 2", video="path/to/video2.mp4"
    )
    routine1 = Routine.objects.create(
        apparatus=apparatus1, label="Routine 1", video="path/to/video1.mp4"
    )
    # Label sorts last globally, so a label-first ordering would move this
    # routine to the end instead of keeping it first on position.
    routine3 = Routine.objects.create(
        apparatus=apparatus2, label="Routine 9", video="path/to/video3.mp4"
    )

    routines_ordered = list(Routine.objects.all())
    assert routines_ordered[0] == routine3  # Apparatus B, Routine 9
    assert routines_ordered[1] == routine1  # Apparatus A, Routine 1
    assert routines_ordered[2] == routine2  # Apparatus A, Routine 2
