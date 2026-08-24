from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from questions.models import Question


@staff_member_required
def preview_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, "questions/preview.html", {"question": question})
