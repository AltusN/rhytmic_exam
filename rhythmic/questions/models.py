from django.db import models


class Apparatus(models.Model):
    name = models.CharField(max_length=50, unique=True)
    position = models.PositiveSmallIntegerField(
        help_text="Display order on reports and score sheets."
    )

    class Meta:
        verbose_name_plural = "apparatus"
        ordering = ["position"]

    def __str__(self) -> str:
        return self.name


class Routine(models.Model):
    apparatus = models.ForeignKey(Apparatus, on_delete=models.PROTECT)
    label = models.CharField(
        max_length=200, help_text="e.g 2006 senior ball, candidate A"
    )
    video = models.FileField(
        upload_to="routines/", help_text="Upload a video file for the routine."
    )

    class Meta:
        ordering = ["apparatus__position", "label"]

    def __str__(self) -> str:
        return f"{self.apparatus.name} - {self.label}"


class Aspect(models.TextChoices):
    DA = "DA", "Apparatus Difficulty"
    DB = "DB", "Body Difficulty"
    AV = "AV", "Artistic Value"
    EX = "EX", "Execution"


class PracticalItem(models.Model):
    routine = models.ForeignKey(
        Routine,
        on_delete=models.PROTECT,
        related_name="items",
        help_text="The routine this item belongs to.",
    )
    aspect = models.CharField(
        max_length=2, choices=Aspect.choices, help_text="e.g 'DA', 'DB', 'AV', 'EX'"
    )
    expert_score = models.DecimalField(
        max_digits=4, decimal_places=2, help_text="Expert score for this item."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["routine", "aspect"], name="uq_one_item_per_aspect_per_routine"
            )
        ]

    def __str__(self) -> str:
        return f"{self.routine} - {self.aspect} - {self.expert_score}"
