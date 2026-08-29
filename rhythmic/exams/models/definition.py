from django.db import models

from questions.models import Aspect


class ExamKind(models.TextChoices):
    PRACTICAL = "PRACTICAL", "Practical"
    THEORY = "THEORY", "Theory"


class MarkingScheme(models.TextChoices):
    CHOICE = "CHOICE", "Choice"
    NUMERIC = "NUMERIC", "Numeric"


class Exam(models.Model):
    level = models.PositiveSmallIntegerField(help_text="The level of the sitting judge")
    year = models.PositiveSmallIntegerField(help_text="The year of the exam")
    kind = models.CharField(
        max_length=9, choices=ExamKind.choices, help_text="The kind of the exam"
    )

    class Meta:
        ordering = ["-year", "level", "kind"]
        constraints = [
            # This is the natural business key: each level/year/kind combination identifies
            # one exam, and the unique constraint enforces that business identity.
            models.UniqueConstraint(
                fields=["level", "year", "kind"], name="uq_one_exam_per_level_year_kind"
            ),
            models.CheckConstraint(
                condition=models.Q(kind__in=ExamKind.values),
                name="ck_exam_kind_is_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.year} - Level {self.level} - {self.kind}"


class ExamComponent(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="components")
    name = models.CharField(
        max_length=50,
        help_text="The name of the exam component i.e 'Apparatus Difficulty'",
    )
    position = models.PositiveSmallIntegerField(
        help_text="The position of the exam component in the exam"
    )
    marking_scheme = models.CharField(
        max_length=7,
        choices=MarkingScheme.choices,
        help_text="The marking scheme for this component",
    )
    aspect = models.CharField(
        max_length=2,
        choices=Aspect.choices,
        blank=True,
        help_text="The aspect of the exam component i.e. 'DA' or '' if theory",
    )

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["exam", "position"], name="uq_one_component_position_per_exam"
            ),
            models.UniqueConstraint(
                fields=["exam", "aspect"], name="uq_one_component_per_aspect_per_exam"
            ),
            models.CheckConstraint(
                condition=models.Q(marking_scheme__in=MarkingScheme.values),
                name="ck_component_marking_scheme_is_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.exam} - {self.name} - {self.position} - {self.marking_scheme}"


__all__ = ["Exam", "ExamKind", "ExamComponent", "MarkingScheme"]
