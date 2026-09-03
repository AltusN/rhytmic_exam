---
name: mutation-sweep
description: Use when running rhythmic/tools/mutation_sweep.py, adding mutants to its catalogue, or interpreting its SURVIVED/KILLED/UNAPPLIED verdicts — covers test scoping, which mutants need a fresh database, and where a claim actually lives.
---

# Running the mutation sweep

Run from `rhythmic/`:

```bash
../.venv/bin/python tools/mutation_sweep.py
```

It breaks one claim at a time and checks that a test objects. A SURVIVED mutant is a
change to the code nobody noticed.

## Scoping and the survivor guard

**The sweep scopes each mutant to its app's tests, cheapest file first** (`86d24a4`). It ran
everything for every mutant and had started exceeding two minutes. The cost turned out to be
test selection, not the database — `--create-db` is only 0.6s dearer than `--reuse-db`, while
`test_admin` is 3.9s and `test_preview` 2.4s against 0.3-0.8s for every other file. Scoping
took an exams mutant from 6.2s to 0.7s and the whole run to 82s, verdicts unchanged.

**A mutant that survives its scope is re-run against everything before being reported**, and
that guard is the point. A KILLED verdict holds whatever the scope, because a test objected;
a SURVIVED verdict does not, because the killing test may not have run. Not parallelised
deliberately: the sweep mutates files in the working tree, so concurrent workers would each
need a git worktree and their own test database.

## Where to mutate, and which mutants need a fresh database

**Mutate where the claim actually lives, and know which ones need a fresh database.**
A `UniqueConstraint` or `CheckConstraint` is DDL: it must be mutated in the
**migration**, because the test database is built from migrations and not from
`models.py`. `Meta.ordering`, `default=`, `__str__` and `on_delete` produce no DDL, so
they are mutated in the **model** — pointing an ordering mutant at a migration's
`options` dict is unfalsifiable in both directions, and reported `UNAPPLIED` when it
was tried on 2026-08-27.

**The sweep used to run everything under `--reuse-db`, and that made migration mutants
unfalsifiable** (fixed 2026-08-27, `8f4c345`). pytest-django reuses the existing test
database and never re-applies migrations, so a mutated migration never reached the
schema and came back `SURVIVED`. Verified on `Exam`'s unique constraint: same
mutation, **6 passed** under `--reuse-db`, **2 failed** under `--create-db`. A false
`SURVIVED` is the expensive direction — it reads as a gap in the suite and sends you
to rewrite tests that were already correct. Mutants whose target path contains
`migrations` now get `--create-db`; the rest keep `--reuse-db`.

**`UNAPPLIED` is the sweep's most valuable line and the easiest to skim past.** It
does not mean the claim is safe; it means the tool could not find the code to break,
so it reported *nothing at all* about that claim. Exact-string matching plus a loud
`UNAPPLIED` is what makes the report trustworthy when the code moves underneath it —
a regex would have silently mutated something else. The consequence is that **the
catalogue is maintained alongside the code, exactly like a test**: refactor a model
and the sweep starts reporting less than it did, with no change in the survivor
count. `ordering-routine` went `UNAPPLIED` the moment Task 8 changed the ordering.

**The sweep cannot reach the schema, and that is a finding in itself.** The test
database is built from `questions/migrations/`, not from `models.py`, so renaming
`uq_one_correct_option_per_question` in the model passes the whole suite. Every
constraint test in this project therefore tests the *migration*, and is only as
trustworthy as someone having remembered to run `makemigrations`. Task 8 closed that
with `test_dry_run_makemigrations`, which is what makes the rest mean what they
appear to mean.

New mutants belong in the catalogue as behaviour is added — the file is a record of
what the code claims, which is why it is worth keeping rather than being a one-off
script.

## The survivor re-run must actually run everything

`TEST_PATHS` was `EXAMS_TESTS + QUESTIONS_TESTS` until Task 6 — no `tests/config/`, so
the one test that catches model-versus-migration drift across every app sat outside the
net that is supposed to be the last word. Demonstrated live rather than reasoned about:
reversing `Sitting.Meta.ordering` survives `tests/exams/` and dies against
`tests/config/test_smoke.py::test_dry_run_makemigrations`. That file is now in
`TEST_PATHS` and in no per-app scope, so only survivors pay for it.

Note *how* it kills. `test_dry_run_makemigrations` objects to the model and the
migration disagreeing, not to the ordering being wrong — nothing asserts `Sitting`
ordering anywhere. A KILLED from that test means "you forgot `makemigrations`", never
"this claim is pinned".

**Mutate a `Meta.ordering` by changing it, not by deleting it.** Deleting the line
leaves an empty `class Meta:` and the file will not import, which is unfalsifiable in
both directions.

## Some tests have no mutant, and that is worth knowing rather than hunting

Two from Task 6:

- `test_a_judge_accumulates_sittings_over_years` is **subsumed** by the retake test —
  every mutant that kills the first kills the second, so it adds no coverage on that
  axis.
- The F10 marker cannot be killed at all. The two `ExamKind` members can never collide,
  because `TextChoices` calls `enum.unique` at class creation and the mutation raises
  `ValueError` at *import*; `ck_exam_kind_is_valid` guards the column independently.

Both are **documentation tests**: they record a claim for whoever later proposes
changing it. Don't manufacture a catalogue entry for one, and don't read the absence of
a mutant as a gap in the suite — that is what separates it from a SURVIVED.
