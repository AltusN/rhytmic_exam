from django.db import models


class ExamKind(models.TextChoices):
    PRACTICAL = "PRACTICAL", "Practical"
    THEORY = "THEORY", "Theory"


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


__all__ = ["Exam", "ExamKind"]
