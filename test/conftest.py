import sys

import pytest

sys.path.append(".")

from rhytmic_exam_app.models import User

@pytest.fixture(scope="module")
def new_user():
    user = User(username="jessy", name="James", surname="May", sagf_id = "123", email="james@may.com")
    return user