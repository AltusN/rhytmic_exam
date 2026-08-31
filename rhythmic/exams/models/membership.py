from django.db import models

from exams.models.definition import ExamComponent
from questions.models import PracticalItem, Question


class ComponentQuestion(models.Model):
    component = models.ForeignKey(
        ExamComponent,
        on_delete=models.CASCADE,
        related_name="question_members",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.PROTECT,
        related_name="component_memberships",
    )
    position = models.PositiveSmallIntegerField(
        help_text="The position of the question within the component."
    )

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["component", "position"],
                name="uq_one_question_position_per_component",
            ),
            models.UniqueConstraint(
                fields=["component", "question"], name="uq_one_question_per_component"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.component} - {self.question} (Position: {self.position})"


class ComponentPracticalItem(models.Model):
    component = models.ForeignKey(
        ExamComponent,
        on_delete=models.CASCADE,
        related_name="practical_item_members",
    )
    practical_item = models.ForeignKey(
        PracticalItem,
        on_delete=models.PROTECT,
        related_name="component_memberships",
    )
    position = models.PositiveSmallIntegerField(
        help_text="The position of the practical item within the component."
    )

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["component", "position"],
                name="uq_one_practical_item_position_per_component",
            ),
            models.UniqueConstraint(
                fields=["component", "practical_item"],
                name="uq_one_practical_item_per_component",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.component} - {self.practical_item} (Position: {self.position})"


__all__ = [
    "ComponentQuestion",
    "ComponentPracticalItem",
]
