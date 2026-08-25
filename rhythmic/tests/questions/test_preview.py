import re

import pytest
from django.urls import reverse

from questions.models import Kind, Option, OptionBlock, Question, QuestionBlock


@pytest.mark.django_db
def test_preview_renders_the_stem_and_option(admin_client):
    question = Question.objects.create(reference="Preview Question")

    text_to_assert = "Which apparatus is being shown?"

    QuestionBlock.objects.create(
        question=question,
        position=1,
        kind=Kind.TEXT,
        text=text_to_assert,
    )

    option_texts = [
        "Rope answer",
        "Hoop answer",
        "Ball answer",
        "Ribbon answer",
    ]

    for position, text in enumerate(option_texts, start=1):
        option = Option.objects.create(
            question=question, position=position, is_correct=(position == 2)
        )
        OptionBlock.objects.create(
            option=option,
            position=1,
            kind=Kind.TEXT,
            text=text,
        )

    url = reverse("questions:preview", args=[question.pk])
    response = admin_client.get(url)
    body = response.content.decode("utf-8")

    assert response.status_code == 200
    assert text_to_assert in body
    for text in option_texts:
        assert text in body


@pytest.mark.django_db
def test_preview_does_not_reveal_the_correct_option(admin_client):
    question = Question.objects.create(reference="Private answer question")

    for position, is_correct in [(1, True), (2, False)]:
        option = Option.objects.create(
            question=question, position=position, is_correct=is_correct
        )
        OptionBlock.objects.create(
            option=option,
            position=1,
            kind=Kind.TEXT,
            text="Same visible answer",
        )
    url = reverse("questions:preview", args=[question.pk])
    response = admin_client.get(url)
    body = response.content.decode("utf-8")

    list_items = re.findall(r"<li>(.*?)</li>", body, re.DOTALL)

    assert len(list_items) == 2
    assert len(set(list_items)) == 1


@pytest.mark.django_db
def test_preview_requires_staff_member(client):
    question = Question.objects.create(reference="Staff only question")
    url = reverse("questions:preview", args=[question.pk])
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_preview_rejects_a_signed_in_candidate(client, django_user_model):
    question = Question.objects.create(reference="Candidate access question")
    candidate = django_user_model.objects.create_user(
        username="candidate",
        password="test-password",
        is_staff=False,
    )
    client.force_login(candidate)

    url = reverse("questions:preview", args=[question.pk])
    response = client.get(url)

    assert response.status_code == 302


@pytest.mark.django_db
def test_preview_of_a_missing_question_returns_404(admin_client):
    url = reverse("questions:preview", args=[9999])
    response = admin_client.get(url)
    assert response.status_code == 404
