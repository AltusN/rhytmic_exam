from django.apps import apps


def test_exams_app_exists():
    app = apps.get_app_config(
        "exams"
    )  # This will raise an error if the app is not properly configured

    assert app.models_module is not None
