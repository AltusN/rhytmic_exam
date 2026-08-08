import pytest
from django.contrib.sessions.models import Session
from django.test import Client


def test_admin_login_page_renders():
    client = Client()
    
    response = client.get("/admin/login/")

    assert response.status_code == 200
    assert b"Django administration" in response.content


@pytest.mark.django_db
def test_database_is_reachable():
    # Count the number of sessions in the database to ensure it's reachable
    session_count = Session.objects.count()
    assert session_count == 0  # The count should be exactly 0
