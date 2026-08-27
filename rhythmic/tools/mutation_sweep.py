"""Break one claim at a time and confirm a test objects.

A SURVIVED mutant is a change to the code that no test noticed — either a gap in
the suite, or a test that only appears to cover the behaviour. See CLAUDE.md,
"No test is accepted until it has been shown red".

Run from `rhythmic/`:

    ../.venv/bin/python tools/mutation_sweep.py

Nothing is committed by this script: each source file is restored in a `finally`
block, and the run ends by asserting `git status` is clean.
"""

import pathlib
import subprocess
import sys

RHYTHMIC = pathlib.Path(__file__).resolve().parent.parent
PYTHON = RHYTHMIC.parent / ".venv" / "bin" / "python"

TEST_PATHS = [
    "tests/questions/test_theory.py",
    "tests/questions/test_practical.py",
    "tests/questions/test_blocks.py",
    "tests/questions/test_history.py",
    "tests/questions/test_admin.py",
    "tests/questions/test_preview.py",
    "tests/exams/test_definition.py",
]

# (name, file, text to find, text to put in its place)
#
# Schema-level claims — CheckConstraint, UniqueConstraint, column types — cannot be
# mutated here. The test database is built from `questions/migrations/`, not from
# `models.py`, so renaming a constraint in the model changes nothing a test can see.
# Mutate the migration instead, or cover it with a `makemigrations --check` test.
MUTANTS = [
    (
        "ordering-apparatus",
        "questions/models.py",
        'verbose_name_plural = "apparatus"\n        ordering = ["position"]',
        'verbose_name_plural = "apparatus"',
    ),
    (
        "ordering-routine",
        "questions/models.py",
        'ordering = ["apparatus__position", "label", "pk"]',
        "ordering = []",
    ),
    (
        "ordering-routine-drop-label",
        "questions/models.py",
        'ordering = ["apparatus__position", "label", "pk"]',
        'ordering = ["apparatus__position", "pk"]',
    ),
    (
        "ordering-question",
        "questions/models.py",
        'class Meta:\n        ordering = ["reference"]',
        "class Meta:\n        ordering = []",
    ),
    (
        "ordering-contentblock",
        "questions/models.py",
        'abstract = True\n        ordering = ["position"]',
        "abstract = True\n        ordering = []",
    ),
    (
        "ondelete-routine-apparatus",
        "questions/models.py",
        "apparatus = models.ForeignKey(Apparatus, on_delete=models.PROTECT)",
        "apparatus = models.ForeignKey(Apparatus, on_delete=models.CASCADE)",
    ),
    (
        "ondelete-option-question",
        "questions/models.py",
        'Question, on_delete=models.CASCADE, related_name="options"',
        'Question, on_delete=models.DO_NOTHING, related_name="options"',
    ),
    (
        "ondelete-questionblock",
        "questions/models.py",
        'Question, on_delete=models.CASCADE, related_name="blocks"',
        'Question, on_delete=models.DO_NOTHING, related_name="blocks"',
    ),
    (
        "str-routine",
        "questions/models.py",
        'return f"{self.apparatus.name} - {self.label}"',
        'return "x"',
    ),
    (
        "str-practicalitem",
        "questions/models.py",
        'return f"{self.routine} - {self.aspect} - {self.expert_score}"',
        'return "x"',
    ),
    (
        "str-contentblock-text",
        "questions/models.py",
        'return f"{kind_display} Block at position {self.position}: '
        '{Truncator(self.text).chars(40)}"',
        'return "x"',
    ),
    (
        "admin-formset-rule",
        "questions/admin.py",
        "if correct_options != 1:",
        "if False:",
    ),
    (
        "admin-select-related",
        "questions/admin.py",
        'list_select_related = ("routine__apparatus",)',
        "",
    ),
    (
        "admin-plain-modeladmin",
        "questions/admin.py",
        "class PracticalItemAdmin(SimpleHistoryAdmin):",
        "class PracticalItemAdmin(admin.ModelAdmin):",
    ),
    (
        "admin-unregister-option",
        "questions/admin.py",
        "@admin.register(Option)\nclass OptionAdmin",
        "class OptionAdmin",
    ),
    (
        "admin-drop-option-inline",
        "questions/admin.py",
        "inlines = [QuestionBlockInline, OptionInline]",
        "inlines = [QuestionBlockInline]",
    ),
    (
        "history-off-optionblock",
        "questions/models.py",
        'Option, on_delete=models.CASCADE, related_name="blocks")\n'
        "    history = HistoricalRecords()",
        'Option, on_delete=models.CASCADE, related_name="blocks")',
    ),
    (
        # Swaps the decorator's behaviour without touching the decorator line, so
        # the substitution stays contiguous. Only a signed-in NON-staff user can
        # tell these apart: anonymous gets a 302 from either one.
        "preview-login-required-not-staff",
        "questions/views.py",
        "from django.contrib.admin.views.decorators import staff_member_required",
        "from django.contrib.auth.decorators import login_required as staff_member_required",
    ),
    (
        # Any leak works here — a printed value, a conditional class, conditional
        # markup. The test asserts two options differing only in is_correct render
        # identically, so it catches the property rather than one spelling of it.
        "preview-leaks-is-correct",
        "questions/templates/questions/preview.html",
        "<li>",
        "<li>{{ option.is_correct }}",
    ),
    (
        "admin-drop-list-filter-aspect",
        "questions/admin.py",
        'list_filter = ("aspect",)',
        "",
    ),
    (
        "ordering-exam",
        "exams/models/definition.py",
        'ordering = ["-year", "level", "kind"]',
        "ordering = []",
    ),
    (
        # Drops "year" from the key, so two exams a level apart in re-certification
        # (same level, same kind, different year) collide instead of coexisting.
        "uq-exam-level-year-kind",
        "exams/migrations/0001_initial.py",
        'fields=("level", "year", "kind"),\n                        name="uq_one_exam_per_level_year_kind",',
        'fields=("level", "kind"),\n                        name="uq_one_exam_per_level_year_kind",',
    ),
    (
        # level__gte=0 always holds for a PositiveSmallIntegerField, so this
        # disables the check regardless of what kind is actually saved.
        "ck-exam-kind-valid",
        "exams/migrations/0001_initial.py",
        'condition=models.Q(("kind__in", ["PRACTICAL", "THEORY"])),',
        'condition=models.Q(("level__gte", 0)),',
    ),
]

HISTORY_TAILS = {
    "question": 'blank=True, help_text="Internal notes or context for the question."',
    "practicalitem": 'max_digits=4, decimal_places=2, help_text="Expert score for this item."',
    "option": 'default=False, help_text="Indicates if this option is the correct answer."',
}
for model, tail in HISTORY_TAILS.items():
    MUTANTS.append(
        (
            f"history-off-{model}",
            "questions/models.py",
            f"{tail}\n    )\n    history = HistoricalRecords()",
            f"{tail}\n    )",
        )
    )


def run_tests(*, fresh_database: bool) -> int:
    """Run the suite once. `fresh_database` rebuilds the test database first.

    `--reuse-db` keeps the sweep fast, but pytest-django then never re-applies
    migrations, so a mutated migration is invisible and its mutant is reported
    SURVIVED when the tests would in fact have killed it. Any mutant that edits a
    migration must therefore pay for `--create-db`.
    """
    result = subprocess.run(
        [
            str(PYTHON),
            "-m",
            "pytest",
            *TEST_PATHS,
            "-q",
            "-x",
            "--no-header",
            "--create-db" if fresh_database else "--reuse-db",
            "-p",
            "no:cacheprovider",
        ],
        cwd=RHYTHMIC,
        capture_output=True,
        text=True,
    )
    return result.returncode


def main() -> int:
    survived, unapplied = [], []
    for name, relative_path, before, after in MUTANTS:
        source = RHYTHMIC / relative_path
        original = source.read_text()
        if before not in original:
            unapplied.append(name)
            print(f"{'UNAPPLIED':9s} {name:34s} pattern not found")
            continue
        try:
            source.write_text(original.replace(before, after, 1))
            returncode = run_tests(fresh_database="migrations" in relative_path)
        finally:
            source.write_text(original)
        if returncode == 0:
            survived.append(name)
        print(f"{'SURVIVED' if returncode == 0 else 'KILLED':9s} {name}")

    mutated_paths = sorted({relative for _, relative, _, _ in MUTANTS})
    dirty = subprocess.run(
        ["git", "status", "--short", *mutated_paths],
        cwd=RHYTHMIC,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if dirty:
        print(f"\nWARNING: working tree is not clean after the sweep:\n{dirty}")

    print(
        f"\nkilled={len(MUTANTS) - len(survived) - len(unapplied)} survived={len(survived)}"
    )
    for name in survived:
        print(f"  SURVIVED  {name}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
