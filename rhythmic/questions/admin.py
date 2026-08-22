from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import BaseInlineFormSet
from simple_history.admin import SimpleHistoryAdmin

from questions.models import (
    Apparatus,
    Option,
    OptionBlock,
    PracticalItem,
    Question,
    QuestionBlock,
    Routine,
)


@admin.register(Apparatus)
class ApparatusAdmin(admin.ModelAdmin):
    list_display = ("name", "position")


@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ("label", "apparatus")
    list_filter = ("apparatus",)


@admin.register(PracticalItem)
class PracticalItemAdmin(SimpleHistoryAdmin):
    list_display = ("routine", "aspect", "expert_score")
    list_filter = ("aspect",)
    list_select_related = ("routine__apparatus",)


class QuestionBlockInline(admin.TabularInline):
    model = QuestionBlock
    extra = 1


class OptionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        correct_options = 0
        for form in self.forms:
            if not form.cleaned_data.get("DELETE", False) and form.cleaned_data.get(
                "is_correct"
            ):
                correct_options += 1
        if correct_options != 1:
            raise ValidationError("There must be exactly one correct option.")


class OptionInline(admin.TabularInline):
    model = Option
    extra = 1
    formset = OptionInlineFormSet


class OptionBlockInline(admin.TabularInline):
    model = OptionBlock
    extra = 1


@admin.register(Question)
class QuestionAdmin(SimpleHistoryAdmin):
    inlines = [QuestionBlockInline, OptionInline]
    list_display = ("reference",)
    search_fields = ("reference",)


@admin.register(Option)
class OptionAdmin(SimpleHistoryAdmin):
    inlines = [OptionBlockInline]
    list_display = ("question", "position", "is_correct")
    search_fields = ("question__reference",)
    list_filter = ("is_correct",)
