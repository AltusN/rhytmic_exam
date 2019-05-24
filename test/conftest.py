import pytest

from rhytmic_exam_app.models import User

@pytest.fixture(scope="module")
def new_user():
    user = User(name="James", surname="May", sagf_id = "123", email="james@may.com")
    return user