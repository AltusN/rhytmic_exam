import pytest
from django.apps import apps
from django.db import IntegrityError
from django.db.models import ProtectedError

from questions.models import Apparatus, Routine


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
