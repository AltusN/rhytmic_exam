# Questions App Implementation Plan

> **Tutoring mode — this plan deviates from the standard format.**
> Altus writes every line of model, view and test code. Claude explains concepts,
> reviews what is written, and pushes back — Claude does not implement.
>
> | Category | Who produces it | Why |
> |---|---|---|
> | `startapp` output, generated migrations | run the command | Same class as `startproject`. |
> | Settings blocks, `INSTALLED_APPS` entries | shown here | Configuration. |
> | **One worked model** (`Apparatus`, Task 2) | shown here | Django's model syntax needs seeing once. |
> | **Every other model** | **Altus writes** | Fields and constraints are decisions. Specified as tables; the code is his. |
> | Tests | **Altus writes** | Cases and expected values given; code is not. |

**Goal:** The content half of the exam — routines and practical items, theory
questions and their composable content blocks — authorable in the Django admin,
with a preview that shows an official what a candidate will see.

**Architecture:** One Django app, `questions/`, holding content and nothing else. It
knows nothing about levels, exams, sittings or who sits what. Two independent model
families that share no base: the practical side (`Apparatus`, `Routine`,
`PracticalItem`) and the theory side (`Question`, `Option`, and their content
blocks).

**Tech Stack:** Django 6.1, Postgres 17, `Pillow` for `ImageField`,
`django-simple-history` for attributed edits, `pytest-django`.

## Global Constraints

- **`rhythmic/scoring/` stays framework-free.** Nothing in this plan imports from it
  or into it. Marking happens later, in the exams app, by handing plain data across.
- **`Decimal` for every score, never `float`.** `DecimalField`, never `FloatField`.
- **No real exam content in this repository. It is public.** Fixtures and test data
  are synthetic. Uploaded media is gitignored.
- **Check `git status` before committing.** `git commit` commits the whole index.
- **Commit messages follow Conventional Commits**, scope `questions`.
- **Run ruff and pytest from `rhythmic/`.** The pre-commit hook does the same.
- **Postgres must be running** for the suite: `docker compose up -d` from the root.

## What this app is not

**No levels, no exams, no membership, no selection.** A `Question` does not know
which levels sit it; a `PracticalItem` does not know which exam contains it.
`ExamComponent` owns those relationships and lives in the exams app.

**F9 and F10 are therefore not in this plan.** F9 is about which questions a
candidate is given; F10 is about a component that was never sat. Both are
membership questions. They land in the exams/sittings plan.

## Where this lives

Everything is inside `rhythmic/`, and **every path and command below is relative to
that directory** unless it says otherwise. Start with `cd rhythmic`.

**The `git` steps run from the repository root**, because their paths are shown
root-relative. Git resolves pathspecs against your current directory.

## File structure at the end of this plan

```
rhythmic/
├── config/
│   ├── settings.py          + questions, simple_history, MEDIA_*
│   └── urls.py              + questions urls, + media serving in DEBUG
├── media/                   NOT COMMITTED. Uploaded files land here.
├── questions/
│   ├── __init__.py
│   ├── admin.py             inlines for blocks and options; preview link
│   ├── apps.py
│   ├── migrations/
│   ├── models.py            all eight models
│   ├── urls.py
│   ├── views.py             the preview view
│   └── templates/questions/
│       ├── preview.html
│       └── _block.html      renders one content block by kind
└── tests/
    ├── test_questions_practical.py
    ├── test_questions_theory.py
    ├── test_questions_blocks.py
    └── test_questions_preview.py
```

**One `models.py`, not a package.** Eight models is roughly 200 lines and Django's
convention is a single module; splitting adds `__init__` re-export machinery for no
present benefit. If it passes ~400 lines, split it into `models/practical.py` and
`models/theory.py` then — not now.

## The models, in full

Written out here once so the tasks can refer back rather than repeat.

```
Apparatus        name, position                       a table, not choices
Routine          apparatus FK, video, label           exists once
PracticalItem    routine FK, aspect, expert_score     no blocks, no options

Question         reference, notes                     the theory question
  QuestionBlock  question FK + ContentBlock fields
Option           question FK, position, is_correct
  OptionBlock    option FK + ContentBlock fields

ContentBlock     abstract: kind, position, text, image
```

`QuestionBlock` and `OptionBlock` inherit `ContentBlock`, which is abstract — it
creates no table of its own, and each child gets its own with the inherited columns.

---

### Task 1: Create the app and wire it in

**Files:**
- Create (generated): `questions/` via `startapp`
- Modify: `config/settings.py` — `INSTALLED_APPS`
- Create: `tests/test_questions_practical.py`

**Why this is its own task:** an app that is created but not in `INSTALLED_APPS` is
invisible to Django — no migrations, no admin, no models. That failure is silent, so
it gets its own gate.

- [x] **Step 1: Generate the app**

```bash
../.venv/bin/python manage.py startapp questions
```

- [x] **Step 2: Add it to `INSTALLED_APPS`**

In `config/settings.py`, after the `django.contrib.*` entries:

```python
    "questions",
```

- [x] **Step 3: Write the failing test**

One test in `tests/test_questions_practical.py`. It asserts the app is installed and
loadable — `django.apps.apps.get_app_config("questions")` returns a config whose
`name` is `"questions"`. No database needed, so no `django_db` marker.

You write it. The construct you need is `from django.apps import apps`.

- [x] **Step 4: Run it**

```bash
../.venv/bin/python -m pytest tests/test_questions_practical.py -v
```

Expected: PASS once Step 2 is done, and `LookupError: No installed app with label
'questions'` if you skip Step 2. Try it both ways — that error is what the test
exists to catch.

- [x] **Step 5: Full suite and lint**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
```

Expected: **84 passed**, clean, clean.

- [x] **Step 6: Commit**

```bash
git status --short
git add rhythmic/questions/ rhythmic/config/settings.py rhythmic/tests/test_questions_practical.py
git commit
```

Subject: `feat(questions): add the questions app`

**Review gate:** Claude checks the generated app is registered and that the test
fails for the right reason when the registration is removed.

---

### Task 2: `Apparatus` and `Routine`, with media upload

**Files:**
- Modify: `questions/models.py`, `config/settings.py`, `config/urls.py`,
  `pyproject.toml` (add `Pillow`), `.gitignore` (add `media/`)
- Create: `questions/migrations/0001_initial.py` (generated)
- Modify: `tests/test_questions_practical.py`

**Interfaces produced:** `Apparatus(name, position)`,
`Routine(apparatus, label, video)`. Task 3 consumes `Routine`.

**The concept — `MEDIA_ROOT` versus `STATIC_ROOT`.** Static files are yours and ship
with the code: CSS, JavaScript, logos. Media files are uploaded at runtime by users
and must not be in the repository. They are configured, served and deployed
differently, and conflating them is how the legacy tree ended up with 117 exam images
tracked in git.

- [x] **Step 1: Add `Pillow` and the media settings**

`Pillow` goes in the `web` extra of `pyproject.toml` — Django's `ImageField`
requires it, and Task 5 introduces one:

```toml
web = [
    "django >= 6.1",
    "psycopg[binary] >= 3.3",
    "python-dotenv >= 1.2",
    "Pillow >= 12.3"
]
```

Then install: `.venv/bin/pip install -e "rhythmic[dev,web]"` from the repo root.

In `config/settings.py`, beside the existing `STATIC_URL`:

```python
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

- [x] **Step 2: Serve media in development**

Django does not serve uploaded files in production — a real deployment puts them
behind nginx or object storage. For development, add to `config/urls.py`:

```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

The `if settings.DEBUG` guard is not decoration: `static()` returns an empty list
when `DEBUG` is false, but writing it unguarded invites someone to "fix" it later.

- [x] **Step 3: Gitignore uploaded media**

Add to the root `.gitignore`:

```
# Uploaded media. Never committed.
rhythmic/media/
```

- [x] **Step 4: Write `Apparatus` — this one is shown**

Django model syntax needs seeing once. This is the whole model:

```python
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
```

Four things worth understanding rather than copying:

- `unique=True` puts a real `UNIQUE` index in Postgres. Two apparatus named "Ball"
  becomes impossible at the database, not merely discouraged in a form.
- `ordering` gives every query a default sort. Without it, Postgres may return rows
  in any order — and "any order" is usually consistent right up until it isn't.
- `verbose_name_plural` exists because Django would otherwise render "Apparatuss" in
  the admin. Its default pluraliser appends "s".
- `__str__` is what the admin shows in dropdowns. Without it you get
  `Apparatus object (3)`.

- [x] **Step 5: Write `Routine` — you write this one**

| field | type | notes |
|---|---|---|
| `apparatus` | `ForeignKey(Apparatus)` | `on_delete=models.PROTECT` |
| `label` | `CharField(max_length=200)` | e.g. "2026 senior ball, candidate A" |
| `video` | `FileField(upload_to="routines/")` | **not** `ImageField` |

`on_delete=PROTECT`, not `CASCADE`: deleting an apparatus that routines reference
should raise, not silently delete the routines and every practical item built on
them. `CASCADE` is Django's most-used option and almost always the wrong default for
reference data.

Give it a `__str__` and a sensible `Meta.ordering`.

- [x] **Step 6: Make and apply the migration**

```bash
../.venv/bin/python manage.py makemigrations questions
../.venv/bin/python manage.py migrate
```

Read the generated migration before applying it. Migrations are generated, so they
are not yours to write — but they are yours to check.

- [x] **Step 7: Write the failing tests**

In `tests/test_questions_practical.py`. All need `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_apparatus_orders_by_position` | create three apparatus out of order; `Apparatus.objects.all()` returns them by `position` |
| `test_apparatus_name_is_unique` | creating a second "Ball" raises `IntegrityError` |
| `test_routine_belongs_to_an_apparatus` | a routine's `apparatus.name` round-trips |
| `test_deleting_an_apparatus_in_use_is_refused` | `apparatus.delete()` with a routine attached raises `ProtectedError` |

**Assert on the bare `Apparatus.objects.all()`, with no `.order_by()` on it.** Adding
`.order_by("position")` supplies the very ordering the test exists to check, so it
passes with `Meta.ordering` deleted — verified by mutation on 2026-08-10, and it is
how the test was first written. A test that specifies the behaviour it is checking
tests the ORM, not the model. The same trap waits wherever ordering is asserted.

For the video, **pass a plain string** — `video="routines/example.mp4"` — which sets
the stored path and writes nothing. `SimpleUploadedFile` through `.create()` deposits
real files into `rhythmic/media/` on every run; an earlier draft of this plan
recommended it and was wrong.

For the exception tests, `pytest.raises(IntegrityError)` and
`pytest.raises(ProtectedError)`; import `ProtectedError` from `django.db.models`.

`test_apparatus_name_is_unique` needs care: an `IntegrityError` breaks the
transaction, so anything after it in the same test will fail confusingly. Keep the
`pytest.raises` block the last thing in that test.

- [x] **Step 8: Run**

```bash
../.venv/bin/python -m pytest tests/test_questions_practical.py -v
```

Expected: 4 new tests pass, plus Task 1's.

- [x] **Step 9: Full suite, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short          # rhythmic/media/ must NOT appear
git add rhythmic/questions/ rhythmic/config/ rhythmic/pyproject.toml .gitignore rhythmic/tests/test_questions_practical.py
git commit
```

Subject: `feat(questions): add apparatus and routines with uploaded video`
Body: why `PROTECT` over `CASCADE`; why media is separate from static and gitignored.

**Review gate:** Claude reviews the `on_delete` choices and checks no uploaded file
is staged.

---

### Task 3: `PracticalItem`

**Files:**
- Modify: `questions/models.py`, `tests/test_questions_practical.py`
- Create: `questions/migrations/0002_*.py` (generated)

**Interfaces consumed:** `Routine` from Task 2.
**Interfaces produced:** `PracticalItem(routine, aspect, expert_score)`.

**The concept.** This is the whole practical question: watch a routine, enter a
number. There is no stem and there are no options — see `CLAUDE.md`, decided
2026-08-10. One routine has four items, one per aspect, and each carries its own
expert score because a routine's `DA` score is not its `EX` score.

- [x] **Step 1: Write the model — you write this**

| field | type | notes |
|---|---|---|
| `routine` | `ForeignKey(Routine)` | `on_delete=models.PROTECT`, `related_name="items"` |
| `aspect` | `CharField(max_length=2, choices=Aspect)` | a `TextChoices` class |
| `expert_score` | `DecimalField(max_digits=4, decimal_places=2)` | **never** `FloatField` |

`Aspect` is a `models.TextChoices` with four members — `DA`, `DB`, `AV`, `EX` — and
readable labels. **Choices, not a table**, unlike `Apparatus`: the four aspects are
fixed by the FIG Code of Points, whereas apparatus need renaming and reordering by
officials for reporting.

`DecimalField` maps to Postgres `numeric`, which stores decimal digits exactly.
`FloatField` maps to `double precision`, where `0.1 + 0.2` is not `0.3`. F3 is what
that costs when it reaches a mark.

`max_digits=4, decimal_places=2` allows `0.00` to `99.99` — deductions are single
digits, so this is roomy without being silly.

- [x] **Step 2: Add the constraint that matters**

A routine must not have two `DA` items. In `Meta`:

```python
constraints = [
    models.UniqueConstraint(
        fields=["routine", "aspect"], name="one_item_per_routine_and_aspect"
    )
]
```

This is a real `UNIQUE` index in Postgres, so it holds against the admin, a shell, a
management command and a hand-written `INSERT` alike. A `clean()` method would only
hold against forms.

- [x] **Step 3: Migrate**

```bash
../.venv/bin/python manage.py makemigrations questions
../.venv/bin/python manage.py migrate
```

- [x] **Step 4: Write the failing tests**

Add to `tests/test_questions_practical.py`, all `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_a_routine_has_one_item_per_aspect` | create all four aspects for one routine; `routine.items.count() == 4` |
| `test_duplicate_aspect_for_a_routine_is_refused` | a second `DA` for the same routine raises `IntegrityError` |
| `test_expert_score_is_stored_as_decimal` | store `"4.20"`, reload from the database, assert `== Decimal("4.20")` **and** `isinstance(..., Decimal)` |
| `test_the_same_aspect_on_two_routines_is_fine` | `DA` on ball and `DA` on hoop both save |

The third test earns its keep: assert the type as well as the value. A `FloatField`
would satisfy `== Decimal("4.20")` in some cases and fail the `isinstance` check
always — so the type assertion is what actually pins the decision.

Reload with `PracticalItem.objects.get(pk=...)` rather than reusing the in-memory
object. An unreloaded instance still holds whatever Python object you assigned, so
the test would pass without the database having stored anything correctly.

- [ ] **Step 5: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git add rhythmic/questions/ rhythmic/tests/test_questions_practical.py
git commit
```

Subject: `feat(questions): add practical items with per-aspect expert scores`
Body: why the aspect is choices while apparatus is a table; why the uniqueness lives
in a database constraint rather than `clean()`.

**Review gate:** Claude reviews that `expert_score` is `Decimal` end to end, and that
the uniqueness test reloads from the database rather than trusting the instance.

---

### Task 4: `Question` and `Option`

**Files:**
- Modify: `questions/models.py`
- Create: `tests/test_questions_theory.py`, `questions/migrations/0003_*.py`

**Interfaces produced:** `Question(reference, notes)`,
`Option(question, position, is_correct)`. Task 5 attaches blocks to both.

**The concept.** A theory question has no text of its own — its stem is built from
content blocks in Task 5, because a stem may be prose, an image, an image grid, or
several in sequence. What `Question` itself holds is identity and authoring notes.

- [ ] **Step 1: Write the models — you write these**

`Question`:

| field | type | notes |
|---|---|---|
| `reference` | `CharField(max_length=50, unique=True)` | human handle, e.g. "RG-2026-014" |
| `notes` | `TextField(blank=True)` | for officials, never shown to candidates |

`Option`:

| field | type | notes |
|---|---|---|
| `question` | `ForeignKey(Question)` | `on_delete=models.CASCADE`, `related_name="options"` |
| `position` | `PositiveSmallIntegerField()` | display order |
| `is_correct` | `BooleanField(default=False)` | |

**`CASCADE` here, `PROTECT` in Tasks 2 and 3 — the difference is ownership.** An
option has no meaning without its question, so deleting the question should take it.
An apparatus exists independently of the routines referencing it, so deleting one out
from under them should raise.

`blank=True` and `null=True` are different things and both matter. `blank` is a
form-validation rule; `null` is a database column property. For text, use `blank=True`
alone — a `TextField` that is both nullable and blankable has two representations of
"empty", and something will eventually check only one of them.

- [ ] **Step 2: Add the at-most-one-correct constraint**

In `Option.Meta`:

```python
constraints = [
    models.UniqueConstraint(
        fields=["question"],
        condition=models.Q(is_correct=True),
        name="one_correct_option_per_question",
    ),
    models.UniqueConstraint(
        fields=["question", "position"], name="one_option_per_position"
    ),
]
```

The first is a **partial unique index** — unique over `question`, but only across
rows where `is_correct` is true. It makes a second correct answer impossible in the
database.

**Know what it does not do.** It enforces *at most one*, never *at least one*. A
question with zero correct options still saves. "At least one" cannot be expressed as
a constraint on a single row, because the database has nothing to check until the
children exist. It belongs in admin formset validation, which is Task 7 — and until
then a question with no correct answer is possible. That is a real gap, and knowing
exactly where it is beats assuming the constraint covers it.

- [ ] **Step 3: Migrate, then write the failing tests**

`tests/test_questions_theory.py`, all `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_options_order_by_position` | four options created out of order come back sorted |
| `test_a_second_correct_option_is_refused` | marking a second option correct raises `IntegrityError` |
| `test_two_questions_may_each_have_a_correct_option` | the partial index is scoped per question, not global |
| `test_deleting_a_question_deletes_its_options` | `question.delete()`, then `Option.objects.count() == 0` |
| `test_a_question_with_no_correct_option_still_saves` | documents the gap the constraint does not close |

That last one looks like a test for a bug. It is deliberate: it records a known
limitation so that when Task 7 adds formset validation, someone can find this test
and decide whether to change it. An undocumented gap gets rediscovered as a defect
years later.

- [ ] **Step 4: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git add rhythmic/questions/ rhythmic/tests/test_questions_theory.py
git commit
```

Subject: `feat(questions): add theory questions and their options`
Body: `CASCADE` versus `PROTECT` and why they differ here; what the partial unique
index does and does not guarantee.

**Review gate:** Claude reviews the `on_delete` reasoning and checks the
at-least-one gap is recorded rather than assumed away.

---

### Task 5: Content blocks

**Files:**
- Modify: `questions/models.py`
- Create: `tests/test_questions_blocks.py`, `questions/migrations/0004_*.py`

**Interfaces consumed:** `Question` and `Option` from Task 4.
**Interfaces produced:** `QuestionBlock`, `OptionBlock`, both inheriting the abstract
`ContentBlock`.

**The concept — this is what replaces the legacy type 1–5 shapes.** The old app had
five hardcoded question layouts and a `make_type_N_question` function for each. The
five differ only in what the stem is made of and what each option is made of. Blocks
make that data: a stem is an ordered list of blocks, and so is an option. A sixth
layout becomes new rows, not new code.

**An abstract base model creates no table.** `Meta.abstract = True` means Django
generates no migration for `ContentBlock` itself; each concrete child gets its own
table containing the inherited columns. That is what you want here — `QuestionBlock`
and `OptionBlock` share a shape, not storage.

- [ ] **Step 1: Write `ContentBlock` — you write this**

Abstract, with:

| field | type | notes |
|---|---|---|
| `kind` | `CharField(max_length=10, choices=Kind)` | `TEXT`, `IMAGE`, `VIDEO` |
| `position` | `PositiveSmallIntegerField()` | order within its parent |
| `text` | `TextField(blank=True)` | used when `kind` is `TEXT` |
| `image` | `ImageField(upload_to="blocks/", blank=True)` | used when `kind` is `IMAGE` |
| `video` | `FileField(upload_to="blocks/", blank=True)` | used when `kind` is `VIDEO` |

`Meta` carries `abstract = True`, `ordering = ["position"]`, and the kind constraint
below.

The spec's vocabulary lists an *image-grid* as well. Leave it out — and as of
2026-08-15 that deferral is confirmed rather than assumed. `rhytmic_master.db` shows
grids are always four columns, occur twelve times, and are four image references
sharing a location; crucially **a grid never co-occurs with loose images in the same
question** (44 questions have standalone media only, 3 have a grid only). So four
image blocks in sequence captures the content losslessly, and the four-up layout can
be added later without ambiguity about which images it applies to. See F13.

**Decision, 2026-08-15: `kind` and the payload fields are constrained, not merely
documented.** Three kinds against three payload fields is nine combinations of which
three are valid. A `kind=IMAGE` row with no image renders as nothing, in a
candidate's exam, with no error anywhere.

Unlike Task 4's at-least-one-correct-option, this *is* expressible as a row
constraint — that gap existed because the database has nothing to check until child
rows are inserted, and the argument does not transfer. The constraint requires the
kind's own field to be non-empty **and the other two to be empty**, because permitting
both `text` and `image` on one block gives it two contents and lets a renderer
switching on `kind` silently drop one.

```python
models.CheckConstraint(
    condition=(...),
    name="%(app_label)s_%(class)s_kind_matches_payload",
)
```

Two things to know. `CheckConstraint` takes `condition=` on Django 5.1+; the `check=`
kwarg most tutorials still show raises `TypeError` on 6.1. And constraint names must be
unique across the whole database, so a literal name in an abstract base collides the
moment the second child inherits it — `%(app_label)s_%(class)s` is interpolated per
concrete child.

**Consequence to accept now:** this forbids reusing `text` as a caption or alt-text on
an image block. When accessibility needs one, it gets its own field rather than
overloading `text`, which keeps the constraint valid.

- [ ] **Step 2: Write the two concrete children**

`QuestionBlock(ContentBlock)` with `question = ForeignKey(Question,
on_delete=models.CASCADE, related_name="blocks")`.

`OptionBlock(ContentBlock)` with `option = ForeignKey(Option,
on_delete=models.CASCADE, related_name="blocks")`.

Both `CASCADE` — a block has no meaning without its parent.

**Decision, 2026-08-15: position is unique per parent, and deferred.**

```python
models.UniqueConstraint(
    fields=["question", "position"],
    deferrable=models.Deferrable.DEFERRED,
    name="uq_one_block_per_position_per_question",
)
```

Without it, two stem blocks at the same position come back in whatever order Postgres
chooses, so **the same question can read differently to different candidates** and
nothing reports an error. Non-deterministic stem order is a defect in an exam that has
to survive a dispute, not an untidiness.

`DEFERRED` because swapping positions 1 and 2 inside one transaction violates an
immediate constraint mid-way. Deferring the check to commit makes a programmatic
swap work at all — a data migration, a management command, an import.

**It does not make an admin reorder work, and an earlier version of this plan said it
did.** Verified 2026-08-22: posting a swap through the admin is rejected by
`ModelForm._post_clean()`, which runs `validate_unique()` — a `SELECT` for a
conflicting row — *before* any `UPDATE` is emitted. The write never happens, so
whether the database would have deferred its check is irrelevant. Deferral is
necessary for an admin reorder but not sufficient; the form layer has to be bypassed
too, which is a custom formset that renumbers positions from form order. Not built.

`Option`'s equivalent constraint from Task 4 is *not* deferred, and it does not need
to be for Task 7 — the form layer rejects the swap either way. The cost of deferring: Postgres cannot use a deferrable constraint for
`ON CONFLICT` inference, so `bulk_create(update_conflicts=True)` against it will not
work. That only matters if the legacy import ever upserts blocks.

**This constraint cannot live in the abstract base** — it names `question` on one
child and `option` on the other. So each child declares its own `Meta`, and that is
where two silent traps live:

```python
class Meta(ContentBlock.Meta):
    constraints = ContentBlock.Meta.constraints + [...]
```

A bare `class Meta:` drops the inherited `ordering`, and the ordering test would then
pass while testing nothing. And `constraints` is a plain list attribute — declaring it
in the child **replaces** the inherited list rather than extending it, so the kind
constraint disappears from that table with no error at all. `sqlmigrate` is how you
catch both.

- [ ] **Step 3: Migrate and confirm the abstract base made no table**

```bash
../.venv/bin/python manage.py makemigrations questions
../.venv/bin/python manage.py migrate
docker compose -f ../compose.yaml exec -T db psql -U rhythmic -d rhythmic -c '\dt questions*'
```

Expected: tables for `questions_questionblock` and `questions_optionblock`, and
**no** `questions_contentblock`. Seeing that absence is the point of the step.

- [ ] **Step 4: Write the failing tests**

`tests/test_questions_blocks.py`, all `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_a_stem_is_an_ordered_list_of_blocks` | three blocks created out of order come back by `position` |
| `test_an_option_carries_its_own_blocks` | an option's blocks are independent of its question's |
| `test_deleting_a_question_deletes_its_blocks` | count drops to zero |
| `test_contentblock_has_no_table_of_its_own` | `ContentBlock._meta.abstract is True` |
| `test_a_text_block_without_text_is_refused` | `kind=TEXT` with empty `text` raises `IntegrityError` |
| `test_an_image_block_carrying_text_is_refused` | the *other* half of the kind constraint — one payload only |
| `test_the_kind_constraint_applies_to_option_blocks_too` | proves `%(class)s` gave `OptionBlock` its own copy, not that `QuestionBlock` took it |
| `test_two_blocks_cannot_share_a_position` | `IntegrityError` on duplicate `(question, position)` |
| `test_two_questions_may_use_the_same_positions` | the uniqueness is scoped per parent |
| `test_a_type_one_question_is_text_stem_and_text_options` | build the legacy type 1 shape end to end: one text stem block, four options each with one text block, one flagged correct |

Match `IntegrityError` on the constraint name — `pytest.raises(IntegrityError,
match="...")` — for the two kind tests. Both constraints raise the same exception
class, so without the name you cannot tell which one fired, and a test that passes for
the wrong reason is the defect this project keeps rediscovering.

The `OptionBlock` test is not redundancy. The kind constraint is declared once on the
abstract base and templated per child; if the child's `Meta` replaces `constraints`
instead of extending it, `QuestionBlock` keeps the constraint and `OptionBlock`
silently loses it. Only a test against the second child sees that.

**A deferred constraint is not checked until `COMMIT`, and `django_db` never commits.**
Verified 2026-08-15 by probe: creating two blocks with the same `(question, position)`
inside a `@pytest.mark.django_db` test inserts **both rows with no error**, and the
`IntegrityError` then surfaces during teardown — pytest reports an `ERROR` against a
fixture on a test that otherwise passed. A `pytest.raises` around the second `create()`
therefore passes whether the constraint exists or not.

The two constraint families differ, and the tests must respect it:

| constraint | checked | in a test |
|---|---|---|
| `CHECK` (kind matches payload) | on every row write | `pytest.raises` works unchanged |
| `UNIQUE ... DEFERRABLE INITIALLY DEFERRED` | at `COMMIT` | must be forced immediate first |

Force it inside the test's transaction, before the inserts:

```python
with connection.cursor() as cursor:
    cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
```

`connection` from `django.db`. Both position tests need it, so it belongs in a fixture
rather than being typed twice.

Give the fixture `db` as a parameter. **Not because it fails without it** — verified
2026-08-15 that a fixture with no `db` parameter still forces the constraints
successfully, because pytest-django's `_django_db_marker` is autouse and autouse
fixtures run before non-autouse ones at the same scope. Declare `db` to state the
dependency and to stop depending on a plugin's internal ordering, not to fix a break.

**This was expected to apply again at Task 7 and does not.** `Option`'s
`uq_unique_option_position_per_question` stays immediate — see the note under Task 5
on why deferring it would not have helped the admin — so
`test_duplicate_position_for_the_same_question_is_refused` in
`tests/test_questions_theory.py` keeps working unchanged. The warning stands for
whenever that constraint *is* deferred: it will silently stop testing anything
without the fixture.

That last test is the one that proves the design. Legacy needed
`make_type_one_question` to produce that shape; here it is rows. Name it for the
legacy type it replaces so the connection survives.

- [ ] **Step 5: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short          # rhythmic/media/ must NOT appear
git add rhythmic/questions/ rhythmic/tests/test_questions_blocks.py
git commit
```

Subject: `feat(questions): compose stems and options from content blocks`
Body: that this replaces the five legacy question types; why the abstract base
creates no table; why image-grid is deliberately absent.

**Review gate:** Claude reviews whether the type-1 reconstruction test genuinely
builds the shape rather than asserting a count, and checks no uploaded file is staged.

---

### Task 6: Attributed edit history

**Files:**
- Modify: `pyproject.toml`, `config/settings.py`, `questions/models.py`
- Create: `questions/migrations/0005_*.py`, `tests/test_questions_history.py`

**The concept — why history rather than versions.** The spec considered version
chains and rejected them: sittings freeze their own copy of what they asked, so
editing a question cannot corrupt a historical result. History is not there to
protect results. It is there to answer "who changed this answer key, and when" —
which is a different question, and the one an official actually asks during a
dispute.

- [ ] **Step 1: Install and register**

```toml
web = [
    "django >= 6.1",
    "psycopg[binary] >= 3.3",
    "python-dotenv >= 1.2",
    "Pillow >= 12.3",
    "django-simple-history >= 3.13"
]
```

`.venv/bin/pip install -e "rhythmic[dev,web]"` from the repo root, then add
`"simple_history"` to `INSTALLED_APPS`.

- [ ] **Step 2: Add history to the models that get edited**

`from simple_history.models import HistoricalRecords`, then `history =
HistoricalRecords()` on **`Question`, `Option`, `PracticalItem`, `QuestionBlock` and
`OptionBlock`**.

**Revised 2026-08-18: the two block models were added.** This step originally named
only the first three, because it was written before Task 5 existed. After Task 5,
`Question` carries `reference` and `notes` and nothing else, and `Option` carries
`position` and `is_correct` — **every word a candidate reads lives in a block row.**
History on `Question` and `Option` alone would record who flipped `is_correct` and
say nothing about who reworded the stem or a distractor, and a reworded distractor
can turn a candidate's wrong answer right. That is dispute material by this task's
own standard.

Note the cost, because it is not free: each historical model doubles the writes on
its table, and blocks churn far more than `is_correct` does during authoring.
Accepted deliberately.

Not on `Apparatus` or `Routine`. Ask what question the history answers: "who changed
this answer key" and "who changed this expert score" are dispute material. "Who
renamed Ribbon" is not. Every historical model doubles the writes on that table, so
this is a judgement about value, not a default to apply everywhere.

`HistoricalRecords()` on an **abstract** base does not do what you want — it must go
on each concrete child. Putting it on `ContentBlock` is the thing to check at review.

- [ ] **Step 3: Add the middleware that records *who***

In `config/settings.py`, append to `MIDDLEWARE`:

```python
    "simple_history.middleware.HistoryRequestMiddleware",
```

**Without this, history records what changed but not who.** The middleware attaches
the request's user to the historical row. Changes made in a shell or a management
command have no request and record no user, which is correct — nobody was logged in.

- [ ] **Step 4: Migrate, then write the failing tests**

`tests/test_questions_history.py`, all `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_editing_an_expert_score_records_both_values` | save `4.20`, change to `4.50`, then the item's `history.count() == 2` and the older record still holds `Decimal("4.20")` |
| `test_history_records_the_change_type` | the first historical row's `history_type` is `"+"` (created), the second `"~"` (changed) |
| `test_apparatus_has_no_history` | `hasattr(Apparatus, "history") is False` |
| `test_rewording_a_block_records_both_versions` | edit a `QuestionBlock`'s `text`, then `history.count() == 2` and the older record holds the original wording |
| `test_block_history_survives_deleting_the_question` | delete the question; the block row goes with it, the historical rows do not |

The third test pins a decision rather than a behaviour. Without it, someone adds
`HistoricalRecords()` to every model in a tidying pass and nothing objects.

The fifth is the one that justifies history existing at all. simple_history drops the
`FOREIGN KEY` on the tracked model's own relations — verified in the generated DDL,
where `questions_historicalquestionblock.question_id` is a plain nullable `bigint`
with an index and no constraint. So `Question.delete()` cascades the live block away
and leaves its history standing. An audit record that vanishes with the thing it
audits answers nothing during a dispute.

**Attribution is not testable here.** `history_user_id` is filled by the middleware
from `request.user`, and these tests make no request, so every historical row they
write has a null user. Testing that the middleware works needs the admin client —
it belongs in Task 7.

- [ ] **Step 5: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git add rhythmic/questions/ rhythmic/config/settings.py rhythmic/pyproject.toml rhythmic/tests/test_questions_history.py
git commit
```

Subject: `feat(questions): record attributed edit history on answer keys`
Body: why history rather than version chains; why only three models carry it.

**Review gate:** Claude reviews which models got history and whether the middleware
is registered — history without the middleware looks like it works.

---

### Task 7: The admin

**Files:**
- Modify: `questions/admin.py`
- Create: `tests/test_questions_admin.py`

**The concept.** The admin is the reason this project chose Django — officials author
questions, and generating those screens from model definitions removes the largest
part of the frontend work. Blocks and options are edited **inline**, inside their
parent's page, because authoring a question means composing its stem and answers in
one place.

- [x] **Step 1: Register the practical models**

`Apparatus`, `Routine` and `PracticalItem` with `admin.site.register` or the
`@admin.register` decorator. Give `PracticalItem` a `list_display` of routine,
aspect and expert score, and a `list_filter` on aspect — a screen listing 20 items
with no filter is a screen officials will not use.

- [x] **Step 2: Register the theory models with inlines**

`QuestionAdmin` needs two inlines: `QuestionBlockInline` for the stem and
`OptionInline` for the answers. Both subclass `admin.TabularInline` (or `StackedInline`
if the fields are too wide to read in a row).

`OptionBlock` cannot be inlined inside `QuestionAdmin` — Django's admin does not nest
inlines two deep. Register `Option` separately with its own `OptionBlockInline` so
option content is editable on the option's own page. Discovering that limitation
here, deliberately, beats discovering it while debugging.

- [x] **Step 3: Close the at-least-one-correct gap**

Task 4 left it open: the database enforces at most one correct option, never at
least one. Add a formset validation on `OptionInline` that raises `ValidationError`
unless **exactly one** option is flagged correct.

Exactly-one rather than at-least-one, revised 2026-08-22. Two correct options is not
merely undesirable — it hits `uq_one_correct_option_per_question` as an unhandled
`IntegrityError`, which is a 500 page rather than a form error an author can read.
The database catches it and the admin has no way to render that.

You write this. The construct is a custom `BaseInlineFormSet` with a `clean()`
method, set as `OptionInline.formset`. Inside `clean()`, iterate **`self.forms`** and
read `form.cleaned_data` with `.get()`, skipping forms marked for deletion.

Not `self.cleaned_data`: that is a property which calls `self.is_valid()` and raises
`AttributeError` when any child form failed (`django/forms/formsets.py:277`), so one
bad `position` blows up inside `clean()`. Django's docs work around it with
`if any(self.errors): return`; iterating `self.forms` needs no such guard.

**This is form-layer validation, so it holds only for the admin.** A shell or a
management command can still create a question with no correct answer. That is the
trade recorded in Task 4 — worth knowing rather than assuming closed.

- [x] **Step 4: Write the failing tests**

`tests/test_questions_admin.py`, all `@pytest.mark.django_db`. Use the
`admin_client` fixture — **`pytest-django` provides it**, logged in as a superuser,
so you do not build one.

| test | asserts |
|---|---|
| `test_question_changelist_renders` | GET the question changelist, status `200` |
| `test_practical_item_changelist_renders` | same for practical items |
| `test_anonymous_is_redirected_from_the_admin` | with the plain `client` fixture, GET the changelist, status `302` |
| `test_a_question_with_one_correct_option_is_saved` | the **control**: POST with exactly one correct option; assert `302` and that the option was created |
| `test_a_question_with_no_correct_option_is_rejected` | POST with no option correct; assert the response contains the error and that no option was created |
| `test_a_question_with_two_correct_options_is_rejected` | same, both correct |

**Write the control test first.** The three rejection payloads are long and easy to
get subtly wrong, and a wrong payload still produces the error message — an empty
formset has zero correct options, so `clean()` raises exactly as if the rule had
fired. Two rounds of review on 2026-08-22 passed against a payload whose inline
prefixes were wrong and which never bound at all. Only a test that *succeeds* proves
the payload is well-formed.

**The inline prefix is the FK's `related_name`**, not `<model>_set` —
`BaseInlineFormSet.get_default_prefix()` returns the accessor name
(`django/forms/models.py:1174`). So `options-` and `blocks-` here. Both inlines need
their four management keys (`TOTAL_FORMS`, `INITIAL_FORMS`, `MIN_NUM_FORMS`,
`MAX_NUM_FORMS`) even the one you are not exercising, or the formset never binds and
the page comes back carrying `ManagementForm data is missing`. A checkbox is sent as
`"on"` when ticked and **omitted** when not.

**Posting to the change view rather than the add view is fine and slightly better** —
`question.options.count() == 0` asserts that the option formset specifically saved
nothing, where `Question.objects.count() == 0` only says the page failed somehow.

Reverse the URLs rather than hardcoding them:
`reverse("admin:questions_question_changelist")`. A hardcoded `/admin/questions/...`
path passes until someone changes the admin mount point.

The third test is the F7 lesson as a habit — the legacy `download_results` route had
no authentication and exposed every candidate's scores. Assert it on every admin
screen you add.

- [x] **Step 5: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git add rhythmic/questions/ rhythmic/tests/test_questions_admin.py rhythmic/tests/test_questions_practical.py
git commit
```

Subject: `feat(questions): author questions and routines in the admin`
Body: why blocks and options are inline; that formset validation closes the
at-least-one-correct gap for the admin only; F7 as the reason for the anonymous test.

**Review gate:** Claude reviews whether every registered screen has an
unauthenticated-access test, and whether the formset validation handles the
delete-marked case.

---

### Task 8: Close the gaps the mutation sweep found

**Files:**
- Modify: `tests/test_questions_practical.py`, `tests/test_questions_theory.py`,
  `tests/test_questions_blocks.py`, `tests/test_questions_history.py`,
  `tests/test_questions_admin.py`, `tests/test_django_smoke.py`

Added 2026-08-22 after `tools/mutation_sweep.py` was run against the finished
questions app: 20 mutants, **11 killed and 9 survived**. A survivor is a change to
the code that no test objected to. This task closes them.

**It runs before the preview, and it is not new work.** These are Tasks 2-7 not being
finished: every survivor is a claim made by code that is already committed and
already reviewed. Building the preview first would mean adding the task with the
highest density of vacuous-assertion risk on top of a suite that reports green about
things it does not check.

- [x] **Step 1: The ordering claims**

`ordering-routine` and `ordering-question` survived — `Routine.Meta.ordering` and
`Question.Meta.ordering` are asserted nowhere. `Apparatus` has such a test and it is
the model to copy, including its lesson: **assert on the bare queryset**, never
`.order_by(...)`, or the test supplies the sort it exists to check.

`Routine` is the interesting one, because its ordering is `["apparatus__position",
"label"]` — two apparatus and two labels are needed before the test can tell that
form apart from `["label"]`.

**Done, and it cost a model change.** The `label` key is only observable inside a tie
on `apparatus__position`, and tie order is the planner's choice — Postgres returned
four tied rows in *reverse* insertion order, so the obvious fixture passed with
`label` deleted. `Routine.Meta.ordering` is now
`["apparatus__position", "label", "pk"]`: a total order, no ties, and the fallback is
creation order rather than an arbitrary one. Migration `0006` carries it, and
`sqlmigrate` prints `-- (no-op)` because `AlterModelOptions` emits no DDL.

- [x] **Step 2: `ContentBlock.__str__`**

`str-contentblock-text` survived; the method has four branches (text, image, video,
unsaved) and none is covered. `str-routine` and `str-practicalitem` are killed, so
those two files show the shape.

The image and video branches are the ones worth care: they run
`PurePosixPath(...).name`, so a block with `image="blocks/a/b/c.jpg"` should render
`c.jpg`. The unsaved branch exists only because `RET503` demanded a return.

- [x] **Step 3: History on `Question`, `Option` and `OptionBlock`**

`history-off-question`, `history-off-option` and `history-off-optionblock` all
survived. `test_questions_history.py` covers `PracticalItem` and `QuestionBlock` and
stops there — so **the answer key's own audit trail is the untested half**, which is
exactly backwards: who flipped `is_correct` is the dispute-relevant edit.

Remember historical querysets order newest-first, so `history.first()` is the latest
edit and `history.last()` is the creation.

- [x] **Step 4: The two admin claims**

`admin-select-related` survived — deleting `list_select_related` from
`PracticalItemAdmin` costs 25 queries instead of 5 on a 20-row key and no test
notices. The construct is pytest-django's **`django_assert_num_queries`** fixture.
Assert a number that fails when the second hop is dropped; do not assert a range so
wide it can never fail.

`admin-plain-modeladmin` survived — swapping `SimpleHistoryAdmin` for
`ModelAdmin` breaks nothing, because the history *view* is never requested.
`reverse("admin:questions_practicalitem_history", args=[pk])` and assert both the
old and the new expert score appear. Plain `ModelAdmin` also serves that URL, so the
assertion must be on the values, not on the status code.

`admin-drop-list-filter-aspect` also survived and is deliberately **not** in scope —
it is presentation, and a test pinning it buys less than it costs.

- [x] **Step 5: Models and migrations must agree**

The sweep cannot reach `CheckConstraint`, `UniqueConstraint` or column types at all:
the test database is built from `questions/migrations/`, not from `models.py`.
Renaming `uq_one_correct_option_per_question` in the model passes every test.

So the schema claims are only as good as someone remembering to run
`makemigrations`. Add to `tests/test_django_smoke.py`:

```python
call_command("makemigrations", "--check")
```

from `django.core.management`. It raises `SystemExit` when a model change has no
migration. That single test is what makes every constraint test in the suite mean
what it appears to mean.

**Three things this plan had wrong, all found by running it.** `--dry-run` is
redundant: `makemigrations.py:118` reads `if check_changes: self.dry_run = True`, so
`--check` writes nothing (true since Django 4.2). The test **needs**
`@pytest.mark.django_db`, because `makemigrations` reads `django_migrations` through
a `MigrationLoader` before the autodetector runs. And `SystemExit` derives from
`BaseException`, so `except Exception` cannot catch it — catch `SystemExit` by name
and call `pytest.fail`, which keeps Django's captured operation list *and* puts a
remediation in the short summary line.

- [x] **Step 6: Re-run the sweep, lint, commit**

```bash
../.venv/bin/python tools/mutation_sweep.py     # expect 0 survivors bar list_filter
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git commit
```

Subject: `test(questions): close the gaps the mutation sweep found`
Body: that the sweep is the source; that the answer key's history was the untested
half; that `makemigrations --check` is what makes the constraint tests meaningful.
`test:` is right here rather than `feat:` — this is tests added to code that already
exists, which is the exception the convention reserves it for.

**Review gate:** Claude re-runs `tools/mutation_sweep.py` and reports the survivor
count rather than reading the tests and judging them.

**Done 2026-08-23, `df5f45f`.** 137 tests pass; the sweep is 21 mutants, 20 killed,
1 survived — `admin-drop-list-filter-aspect`, the one declared out of scope. The
catalogue grew by one (`ordering-routine-drop-label`) and `ordering-routine` was
repointed at the three-key ordering after it went `UNAPPLIED`.

**The gate earned itself on Step 5.** `except SystemExit: assert e.code == 1` passes
on *both* paths — no exception means the function falls off the end, and an exception
means the handler agrees the exit code was 1. It was read and approved twice before
being run. Tenth instance of the recurring defect, and the first written after the
red-first rule was adopted.

---

### Task 9: The preview

**Files:**
- Create: `questions/views.py`, `questions/urls.py`,
  `questions/templates/questions/preview.html`,
  `questions/templates/questions/_block.html`, `tests/test_questions_preview.py`
- Modify: `config/urls.py`, `questions/admin.py`

**The concept.** The admin form shows an official a stack of block rows. It cannot
show them what a candidate will see — and "what will this look like" is exactly the
question an author needs answered before publishing. The spec calls for a `[Preview]`
action for this reason, and it is the one piece of candidate-facing rendering in this
plan.

- [x] **Step 1: Write the view**

A staff-only view taking a question's primary key and rendering its blocks and
options in candidate order. You write it.

The constructs: `django.contrib.admin.views.decorators.staff_member_required` as the
decorator — **not** `login_required`, which would let any authenticated candidate
preview a draft question including which option is correct. `get_object_or_404` for
the lookup, so a bad primary key is a 404 rather than a 500.

- [x] **Step 2: Write the templates**

`preview.html` iterates the question's blocks, then its options, and for each option
iterates that option's blocks. `_block.html` renders one block by `kind` — text as a
paragraph, image as an `<img>`, video as a `<video controls>`.

**The preview must not reveal `is_correct`.** It shows what a candidate sees, and a
candidate does not see the answer. Getting this wrong makes the preview useless for
its purpose and leaks the key to anyone who can reach it.

- [x] **Step 3: Wire the URL**

`questions/urls.py` with a `preview` path; include it from `config/urls.py` under a
`questions/` prefix. Name the route so `reverse()` works.

- [x] **Step 4: Add the admin link**

A method on `QuestionAdmin` returning an `<a>` to the preview URL, added to
`list_display`. Mark it with `django.utils.html.format_html` rather than building the
string yourself — that is what escapes the content, and F8 is the legacy version of
getting this wrong.

- [x] **Step 5: Write the failing tests**

`tests/test_questions_preview.py`, all `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_preview_renders_the_stem_and_options` | build a type-1 question; the response contains the stem text and all four option texts |
| `test_preview_does_not_reveal_the_correct_option` | the response does **not** contain the words "correct" or the `is_correct` value |
| `test_preview_requires_staff` | with the plain `client` fixture, status is `302` |
| `test_preview_of_a_missing_question_is_404` | a primary key that does not exist gives `404`, not `500` |

For the second test, assert on absence — `assert b"correct" not in response.content`.
Absence tests are weaker than presence tests by nature, so make the correct option's
text distinctive in the fixture and assert *that* string is present exactly as many
times as the others.

- [x] **Step 6: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git add rhythmic/questions/ rhythmic/config/urls.py rhythmic/tests/test_questions_preview.py
git commit
```

Subject: `feat(questions): preview a question as a candidate sees it`
Body: why `staff_member_required` rather than `login_required`; that the preview
deliberately hides the correct option.

**Review gate:** Claude reviews the permission decorator and whether the
does-not-reveal test could pass vacuously.

**Done 2026-08-24, `797b09f`.** 142 tests pass; the sweep is 23 mutants, 22 killed,
1 survived — `admin-drop-list-filter-aspect`, still out of scope. **The gate caught
both things it was written to catch**, on the first round: the does-not-reveal test
checked for `is_correct`, a string no leak can emit, and the permission test used an
anonymous client, which `login_required` redirects too. Nine of nine — the plan is
closed.

**Red-first is mandatory here.** Every assertion in this task is a substring of a
rendered page, and a Django page is full of strings that have nothing to do with the
row under test — `"DA"` survived a review round in Task 7 because `list_filter`
renders it in the sidebar. Render the page **without** the row, assert the string is
absent, and only then assert it is present. See CLAUDE.md, "No test is accepted until
it has been shown red".

---

## What this plan deliberately leaves out

- **Levels, exams, membership, selection.** They belong to `ExamComponent` in the
  exams app. **F9 and F10 land there**, not here.
- **The image-grid block kind.** A grid is several image blocks plus a layout
  decision, and nothing renders it yet.
- **Migrating the 128 legacy media files.** That is its own job, gated on the block
  renderers existing — and `legacy/` is deleted when it is done.
- **Bulk import.** Legacy imported questions by CSV. Nothing needs it yet, and the
  admin is the authoring surface. **Qualified 2026-08-24:** it is the authoring
  surface but a slow one — an option's text lives in an `OptionBlock`, which
  Django's admin cannot reach from the Question page, so a four-option question
  takes five saves. See CLAUDE.md, "Known limitation".
- **The candidate-facing exam runner.** The React island, last plan.
- **Marking anything.** `scoring/` already does that and this app hands it nothing.

## Next plans, in order

1. **Exams, sittings and the freeze** — `ExamComponent`, membership, the snapshot
   that makes F1 executable. **F9 and F10 land here.**
2. **Accounts, allauth and the roster.**
3. **The React island** — the practical runner.
