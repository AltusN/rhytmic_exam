from pathlib import PurePosixPath

from django.db import models
from django.utils.text import Truncator
from simple_history.models import HistoricalRecords


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
    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["routine", "aspect"], name="uq_one_item_per_aspect_per_routine"
            )
        ]

    def __str__(self) -> str:
        return f"{self.routine} - {self.aspect} - {self.expert_score}"


class Question(models.Model):
    reference = models.CharField(
        max_length=50, unique=True, help_text="e.g. 'RG-2026-014'"
    )
    notes = models.TextField(
        blank=True, help_text="Internal notes or context for the question."
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ["reference"]

    def __str__(self) -> str:
        return self.reference


class Option(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    position = models.PositiveSmallIntegerField(
        help_text="Display order of the option."
    )
    is_correct = models.BooleanField(
        default=False, help_text="Indicates if this option is the correct answer."
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ["position"]
        constraints = [
            models.UniqueConstraint(
                fields=["question"],
                condition=models.Q(is_correct=True),
                name="uq_one_correct_option_per_question",
            ),
            models.UniqueConstraint(
                fields=["question", "position"],
                name="uq_unique_option_position_per_question",
            ),
        ]

    def __str__(self) -> str:
        return f"Option {self.position} for Question {self.question.reference}"


class Kind(models.TextChoices):
    TEXT = "TEXT", "Text"
    IMAGE = "IMAGE", "Image"
    VIDEO = "VIDEO", "Video"


class ContentBlock(models.Model):
    kind = models.CharField(
        max_length=10, choices=Kind.choices, help_text="Type of content block."
    )
    position = models.PositiveSmallIntegerField(
        help_text="Display order of the content block."
    )
    text = models.TextField(blank=True, help_text="Text content for the block.")
    image = models.ImageField(
        upload_to="blocks/", blank=True, help_text="Image content for the block."
    )
    video = models.FileField(
        upload_to="blocks/", blank=True, help_text="Video content for the block."
    )

    class Meta:
        abstract = True
        ordering = ["position"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (
                        models.Q(kind=Kind.TEXT)
                        & ~models.Q(text="")
                        & models.Q(image="")
                        & models.Q(video="")
                    )
                    | (
                        models.Q(kind=Kind.IMAGE)
                        & ~models.Q(image="")
                        & models.Q(text="")
                        & models.Q(video="")
                    )
                    | (
                        models.Q(kind=Kind.VIDEO)
                        & ~models.Q(video="")
                        & models.Q(text="")
                        & models.Q(image="")
                    )
                ),
                name="%(app_label)s_%(class)s_kind_matches_payload",
            )
        ]

    def __str__(self) -> str:
        # Django's type checker doesn't understand that get_kind_display()
        # is always available on a model with choices, so we ignore the type error here.
        kind_display = self.get_kind_display()  # type: ignore
        if self.kind == Kind.TEXT:
            return f"{kind_display} Block at position {self.position}: {Truncator(self.text).chars(40)}"
        if self.kind == Kind.IMAGE:
            return f"{kind_display} Block at position {self.position}: {PurePosixPath(self.image.name).name}"
        if self.kind == Kind.VIDEO:
            return f"{kind_display} Block at position {self.position}: {PurePosixPath(self.video.name).name}"
        return "New block (unsaved)"


class QuestionBlock(ContentBlock):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="blocks"
    )
    history = HistoricalRecords()

    class Meta(ContentBlock.Meta):
        constraints = ContentBlock.Meta.constraints + [
            models.UniqueConstraint(
                fields=["question", "position"],
                deferrable=models.Deferrable.DEFERRED,
                name="uq_unique_block_position_per_question",
            )
        ]


class OptionBlock(ContentBlock):
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="blocks")
    history = HistoricalRecords()

    class Meta(ContentBlock.Meta):
        constraints = ContentBlock.Meta.constraints + [
            models.UniqueConstraint(
                fields=["option", "position"],
                deferrable=models.Deferrable.DEFERRED,
                name="uq_unique_block_position_per_option",
            )
        ]
