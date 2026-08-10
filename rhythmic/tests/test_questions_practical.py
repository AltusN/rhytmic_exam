from django.apps import apps


def test_questions_app_is_installed():
    # Check if the 'questions' app is installed
    assert apps.is_installed("questions"), (
        "The 'questions' app is not installed in the Django project."
    )
