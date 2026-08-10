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

- [ ] **Step 1: Generate the app**

```bash
../.venv/bin/python manage.py startapp questions
```

- [ ] **Step 2: Add it to `INSTALLED_APPS`**

In `config/settings.py`, after the `django.contrib.*` entries:

```python
    "questions",
```

- [ ] **Step 3: Write the failing test**

One test in `tests/test_questions_practical.py`. It asserts the app is installed and
loadable — `django.apps.apps.get_app_config("questions")` returns a config whose
`name` is `"questions"`. No database needed, so no `django_db` marker.

You write it. The construct you need is `from django.apps import apps`.

- [ ] **Step 4: Run it**

```bash
../.venv/bin/python -m pytest tests/test_questions_practical.py -v
```

Expected: PASS once Step 2 is done, and `LookupError: No installed app with label
'questions'` if you skip Step 2. Try it both ways — that error is what the test
exists to catch.

- [ ] **Step 5: Full suite and lint**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
```

Expected: **84 passed**, clean, clean.

- [ ] **Step 6: Commit**

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

- [ ] **Step 1: Add `Pillow` and the media settings**

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

- [ ] **Step 2: Serve media in development**

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

- [ ] **Step 3: Gitignore uploaded media**

Add to the root `.gitignore`:

```
# Uploaded media. Never committed.
rhythmic/media/
```

- [ ] **Step 4: Write `Apparatus` — this one is shown**

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

- [ ] **Step 5: Write `Routine` — you write this one**

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

- [ ] **Step 6: Make and apply the migration**

```bash
../.venv/bin/python manage.py makemigrations questions
../.venv/bin/python manage.py migrate
```

Read the generated migration before applying it. Migrations are generated, so they
are not yours to write — but they are yours to check.

- [ ] **Step 7: Write the failing tests**

In `tests/test_questions_practical.py`. All need `@pytest.mark.django_db`.

| test | asserts |
|---|---|
| `test_apparatus_orders_by_position` | create three apparatus out of order; `Apparatus.objects.all()` returns them by `position` |
| `test_apparatus_name_is_unique` | creating a second "Ball" raises `IntegrityError` |
| `test_routine_belongs_to_an_apparatus` | a routine's `apparatus.name` round-trips |
| `test_deleting_an_apparatus_in_use_is_refused` | `apparatus.delete()` with a routine attached raises `ProtectedError` |

For the video, `django.core.files.uploadedfile.SimpleUploadedFile` gives you a fake
file without touching the disk meaningfully. For the exception tests,
`pytest.raises(IntegrityError)` and `pytest.raises(ProtectedError)`; import
`ProtectedError` from `django.db.models`.

`test_apparatus_name_is_unique` needs care: an `IntegrityError` breaks the
transaction, so anything after it in the same test will fail confusingly. Keep the
`pytest.raises` block the last thing in that test.

- [ ] **Step 8: Run**

```bash
../.venv/bin/python -m pytest tests/test_questions_practical.py -v
```

Expected: 4 new tests pass, plus Task 1's.

- [ ] **Step 9: Full suite, lint, commit**

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

- [ ] **Step 1: Write the model — you write this**

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

- [ ] **Step 2: Add the constraint that matters**

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

- [ ] **Step 3: Migrate**

```bash
../.venv/bin/python manage.py makemigrations questions
../.venv/bin/python manage.py migrate
```

- [ ] **Step 4: Write the failing tests**

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

`Meta` carries `abstract = True` and `ordering = ["position"]`.

The spec's vocabulary lists an *image-grid* as well. Leave it out. A grid is several
image blocks plus a layout decision, and nothing renders it yet — add it when the
renderer exists and you know what it needs. Building it now means guessing.

- [ ] **Step 2: Write the two concrete children**

`QuestionBlock(ContentBlock)` with `question = ForeignKey(Question,
on_delete=models.CASCADE, related_name="blocks")`.

`OptionBlock(ContentBlock)` with `option = ForeignKey(Option,
on_delete=models.CASCADE, related_name="blocks")`.

Both `CASCADE` — a block has no meaning without its parent.

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
| `test_a_type_one_question_is_text_stem_and_text_options` | build the legacy type 1 shape end to end: one text stem block, four options each with one text block, one flagged correct |

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
HistoricalRecords()` on **`Question`, `Option`, and `PracticalItem`**.

Not on `Apparatus` or `Routine`. Ask what question the history answers: "who changed
this answer key" and "who changed this expert score" are dispute material. "Who
renamed Ribbon" is not. Every historical model doubles the writes on that table, so
this is a judgement about value, not a default to apply everywhere.

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

The third test pins a decision rather than a behaviour. Without it, someone adds
`HistoricalRecords()` to every model in a tidying pass and nothing objects.

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

- [ ] **Step 1: Register the practical models**

`Apparatus`, `Routine` and `PracticalItem` with `admin.site.register` or the
`@admin.register` decorator. Give `PracticalItem` a `list_display` of routine,
aspect and expert score, and a `list_filter` on aspect — a screen listing 20 items
with no filter is a screen officials will not use.

- [ ] **Step 2: Register the theory models with inlines**

`QuestionAdmin` needs two inlines: `QuestionBlockInline` for the stem and
`OptionInline` for the answers. Both subclass `admin.TabularInline` (or `StackedInline`
if the fields are too wide to read in a row).

`OptionBlock` cannot be inlined inside `QuestionAdmin` — Django's admin does not nest
inlines two deep. Register `Option` separately with its own `OptionBlockInline` so
option content is editable on the option's own page. Discovering that limitation
here, deliberately, beats discovering it while debugging.

- [ ] **Step 3: Close the at-least-one-correct gap**

Task 4 left it open: the database enforces at most one correct option, never at
least one. Add a formset validation on `OptionInline` that raises `ValidationError`
when no option is flagged correct.

You write this. The construct is a custom `BaseInlineFormSet` with a `clean()`
method, set as `OptionInline.formset`. Inside `clean()`, iterate
`self.cleaned_data`, skipping forms marked for deletion.

**This is form-layer validation, so it holds only for the admin.** A shell or a
management command can still create a question with no correct answer. That is the
trade recorded in Task 4 — worth knowing rather than assuming closed.

- [ ] **Step 4: Write the failing tests**

`tests/test_questions_admin.py`, all `@pytest.mark.django_db`. Use the
`admin_client` fixture — **`pytest-django` provides it**, logged in as a superuser,
so you do not build one.

| test | asserts |
|---|---|
| `test_question_changelist_renders` | GET the question changelist, status `200` |
| `test_practical_item_changelist_renders` | same for practical items |
| `test_anonymous_is_redirected_from_the_admin` | with the plain `client` fixture, GET the changelist, status `302` |
| `test_a_question_with_no_correct_option_is_rejected` | POST the add form with two options, neither correct; assert the response contains the error and `Question.objects.count() == 0` |

Reverse the URLs rather than hardcoding them:
`reverse("admin:questions_question_changelist")`. A hardcoded `/admin/questions/...`
path passes until someone changes the admin mount point.

The third test is the F7 lesson as a habit — the legacy `download_results` route had
no authentication and exposed every candidate's scores. Assert it on every admin
screen you add.

- [ ] **Step 5: Run, lint, commit**

```bash
../.venv/bin/python -m pytest -q && ../.venv/bin/ruff format . && ../.venv/bin/ruff check .
git status --short
git add rhythmic/questions/ rhythmic/tests/test_questions_admin.py
git commit
```

Subject: `feat(questions): author questions and routines in the admin`
Body: why blocks and options are inline; that formset validation closes the
at-least-one-correct gap for the admin only; F7 as the reason for the anonymous test.

**Review gate:** Claude reviews whether every registered screen has an
unauthenticated-access test, and whether the formset validation handles the
delete-marked case.

---

### Task 8: The preview

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

- [ ] **Step 1: Write the view**

A staff-only view taking a question's primary key and rendering its blocks and
options in candidate order. You write it.

The constructs: `django.contrib.admin.views.decorators.staff_member_required` as the
decorator — **not** `login_required`, which would let any authenticated candidate
preview a draft question including which option is correct. `get_object_or_404` for
the lookup, so a bad primary key is a 404 rather than a 500.

- [ ] **Step 2: Write the templates**

`preview.html` iterates the question's blocks, then its options, and for each option
iterates that option's blocks. `_block.html` renders one block by `kind` — text as a
paragraph, image as an `<img>`, video as a `<video controls>`.

**The preview must not reveal `is_correct`.** It shows what a candidate sees, and a
candidate does not see the answer. Getting this wrong makes the preview useless for
its purpose and leaks the key to anyone who can reach it.

- [ ] **Step 3: Wire the URL**

`questions/urls.py` with a `preview` path; include it from `config/urls.py` under a
`questions/` prefix. Name the route so `reverse()` works.

- [ ] **Step 4: Add the admin link**

A method on `QuestionAdmin` returning an `<a>` to the preview URL, added to
`list_display`. Mark it with `django.utils.html.format_html` rather than building the
string yourself — that is what escapes the content, and F8 is the legacy version of
getting this wrong.

- [ ] **Step 5: Write the failing tests**

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

- [ ] **Step 6: Run, lint, commit**

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

---

## What this plan deliberately leaves out

- **Levels, exams, membership, selection.** They belong to `ExamComponent` in the
  exams app. **F9 and F10 land there**, not here.
- **The image-grid block kind.** A grid is several image blocks plus a layout
  decision, and nothing renders it yet.
- **Migrating the 128 legacy media files.** That is its own job, gated on the block
  renderers existing — and `legacy/` is deleted when it is done.
- **Bulk import.** Legacy imported questions by CSV. Nothing needs it yet, and the
  admin is the authoring surface.
- **The candidate-facing exam runner.** The React island, last plan.
- **Marking anything.** `scoring/` already does that and this app hands it nothing.

## Next plans, in order

1. **Exams, sittings and the freeze** — `ExamComponent`, membership, the snapshot
   that makes F1 executable. **F9 and F10 land here.**
2. **Accounts, allauth and the roster.**
3. **The React island** — the practical runner.
