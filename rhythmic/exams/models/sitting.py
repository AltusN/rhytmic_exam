from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from exams.models import Exam


class Status(models.TextChoices):
    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    SUBMITTED = "SUBMITTED", "Submitted"
    CERTIFIED = "CERTIFIED", "Certified"


class Sitting(models.Model):
    judge = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sittings"
    )
    exam = models.ForeignKey(Exam, on_delete=models.PROTECT, related_name="sittings")
    # a sitting that exists but has not started can only have the status PENDING
    status = models.CharField(
        max_length=11, choices=Status.choices, default=Status.PENDING
    )
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    certified_at = models.DateTimeField(null=True, blank=True)
    certified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="certifications_made",
    )
    outcome = models.CharField(max_length=255, blank=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ["exam", "started_at", "pk"]

    def __str__(self) -> str:
        if self.certified_by:
            return f"{self.exam} - {self.judge} - {self.status} - Certified by {self.certified_by}"
        return f"{self.exam} - {self.judge} - {self.status}"
