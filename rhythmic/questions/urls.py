from django.urls import path

from questions import views

app_name = "questions"
urlpatterns = [
    path("preview/<int:question_id>/", views.preview_question, name="preview"),
]
