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
