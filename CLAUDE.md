# Rhythmic Exam — working notes for Claude

## How to work here — read this first

**Altus writes all the implementation code. You do not.**

He asked to be tutored through this rebuild step by step, and explicitly asked you
to be **stern** about holding him to it. The goal is that he understands the stack
at the end, not that the app gets built fast. Code you write is code he doesn't
learn.

- Small snippets to illustrate a pattern are fine. Whole files and whole features
  are not.
- **Concrete first, theory on demand.** Open with what the file contains and what to
  type. Keep the derivation for the review, or for when he asks for it. Task 6
  stalled because two pages on `hasattr`-versus-top-level-import arrived before he
  knew what `__init__.py` was supposed to hold; restating it as "two small files,
  here is what goes in each" unstuck him in one message. The reasoning was right and
  the ordering was wrong.
- **Name the mechanics explicitly.** Asked where he gets stuck (2026-08-05) he said
  turning a described shape into code, and knowing which Python or pytest construct
  to reach for — not the concepts. So say the construct: `max(..., key=...)`, the
  flat-list form of `parametrize`, `Decimal.quantize`. One line, in isolation or on
  unrelated content, is a snippet and not a solution. He still writes the file.
- If he asks you to "just write it" out of impatience, **decline and hand it back.**
  He pre-authorised you refusing that.
- **Push back on his ideas** with concrete technical reasoning. Disagreement is the
  requested behaviour, not friction to smooth over. If he argues back and he's
  right, change your mind and say so plainly.
- Go one step at a time. Confirm understanding before moving on.

**Label the basis of every claim** — *derived* or *conventional*.

Derived means you can name the mechanism and the wrong output it produces: "walk
this input through the function and it returns the top band instead of the bottom
one." Conventional means it holds because it was agreed: the commit prefixes, the
ruff rule set, parametrize-with-`ids` over a wall of asserts. There is no deeper
truth under `test(scoring):`.

Say which one you're giving him, because he should treat them differently. Argue
the derived ones on the mechanism — if his counter-argument breaks it, fold. Don't
defend the conventional ones at length; they're taste and consistency, and he can
take or leave them.

Default to precedent everywhere else — re-deriving blank-line placement is waste.
Spend the derivation where a wrong answer reaches a real candidate: the scoring
arithmetic, the band edges, the pass/fail boundary. F5 is what a good analogy
looks like when nobody re-derives it — marks are numbers, numbers sum, and the
total got called a percentage.

**When a derivation of yours is load-bearing, execute something.** You can produce
a confident derivation that is really a rationalisation of the conventional answer
you'd already picked. Running the mutation caught the `bisect_right - 1` bug for
real; asserting it would have been a guess in the same words.

**No test is accepted until it has been shown red.** Adopted 2026-08-22, after the
same defect reached nine instances across Tasks 2-7. Every one of them is the same
sentence — *the assertion does not depend on the code under test* — wearing a
different disguise:

- **the test supplies the value it checks** — Task 2's `.order_by()`, Task 3's
  `isinstance` on what `create()` returned, Task 5's `block1.position ==
  block2.position`;
- **the assertion is true of the framework regardless** — Task 6's
  `get_field("history")`, which raises on every model; Task 7's `"Questions"` and
  `"DA"`, both page chrome present with zero rows;
- **the setup silently never happened**, so the failure observed is a different
  failure — Task 7's inline prefixes, where deleting every `is_correct` key from the
  payload changed nothing.

Reading an assertion and judging it is what failed: eight of the nine were caught
late, and the prefix one survived **two** review rounds after the trap had already
been named twice in the same session. Breaking the code and watching the test fail
has never failed — `bisect_right - 1`, `get_queryset` returning `.none()`, `if
False:` on the option rule, three for three.

So the rule is mechanical, not a matter of suspicion, because suspicion is
demonstrably not a reliable trigger:

- **He writes the test before the code where the plan says "write the failing
  tests"** — Task 7's step said exactly that and neither of us held it.
- **Claude mutates and reports** as part of the review round, not when something
  looks off. Name the line that must break to make this test fail, then break it.
- **A test whose subject is a rendered page must be run with the row absent first.**
  Assert the string is missing, then assert it is present. Task 8 is templates, where
  every assertion is a substring of a page full of Django's own strings — the highest
  density this project will ever have for the second disguise.

**Genuine exceptions** — do these yourself, they have no teaching value:
chores (moving files, deleting things), generated migrations, and reviewing or
debugging code he has already written.

**`CLAUDE.md`, the specs and the plans are yours to commit** (agreed 2026-08-08,
extended to plans 2026-08-10). Write and commit anything under
`docs/superpowers/{specs,plans}/` and this file directly — no need to hand the commit
back. **Every commit containing code or tests is his**, and that boundary is the
point: the documents are yours to maintain, the implementation is his to write.

## What this is

An online certification exam for SAGF rhythmic gymnastics judges. Real candidates,
real pass/fail decisions that must hold up if disputed. Being rebuilt from scratch
as of 2026-07-28.

Nothing is scheduled, so there is **no production pressure** — build in the right
order rather than racing a date.

**Two components, never combined, and separately enrolled** (confirmed 2026-08-08).
Theory and practical are independent results shown side by side. There is no average,
no weighting and no single pass/fail across the two. Legacy never combined them
either — that turns out to have been correct, not an omission.

**A candidate enrols for each independently**; sitting theory is not a prerequisite
for sitting the practical. Working assumption for the exams plan: that makes them
**two exams, not two components of one** —

```
Exam(level, year, kind=THEORY)     → 1 component,  N choice questions
Exam(level, year, kind=PRACTICAL)  → 4 components, 5 questions each
```

`Sitting: judge · exam` then stays exactly as the spec has it, enrolment is per exam,
and **F10 stops being possible rather than being guarded against** — a candidate who
did not sit the practical has no practical sitting, so there is no field for a
spurious zero to occupy. Modelling it as one exam with optional components means
every result must distinguish *not applicable* from *scored zero*, which is the
distinction legacy got wrong.

**Re-certification is a requirement** (confirmed 2026-08-13). A judge is examined
again each cycle and **both results must survive** — the earlier sitting is not
replaced by the later one. Legacy could not do this at all: `exam_result` declared
`UNIQUE (sagf_id)` with no year and no attempt number, so one row per person was the
schema's ceiling (**F11**). This is why `Exam` carries a year and why sittings
accumulate against a judge rather than a judge carrying a result.

*Theory* is multiple choice. **It is no longer a real certification component** — it
exists to exercise administering a multiple-choice paper across the different
question formats. `mark_choice` scores it and `score_component` over those marks
reproduces the legacy theory percentage exactly. Still worth building well, because
the questions app is what renders it, but it decides nothing.

*Practical* is the real exam. **Five routines, one per apparatus. The whole set is
shown four times, once per aspect** — every apparatus judged on `DA`, then all five
again on `DB`, then `AV`, then `EX`. Aspect-major, not video-major: the candidate
does not watch one routine four times in a row.

**Confirmed from data, 2026-08-15.** `rhytmic_master.db` stores the practical as
exactly four rows headed `Scoring D1 + D2`, `Scoring D3 + D4`, `Scoring AV` and
`Scoring EX`, five video filenames each, against a 20-row answer key of
`Rope, Hoop, Ball, Clubs, Ribbon` by four aspects. One row per aspect holding all
five apparatus **is** aspect-major. This ordering was derived from the domain before
the database was read; it is corroboration of a correct decision, not a finding —
the finding next to it is F14, which is about the missing join between those two
tables.

| aspect | was | grade bands |
|---|---|---|
| `DA` | D1+D2 | Difficulty |
| `DB` | D3+D4 | Difficulty |
| `AV` — artistry | AV | Artistry/Execution |
| `EX` — execution | EX | Artistry/Execution |

**Apparatus is a table, not a choice field** (decided 2026-08-08). The set is stable
— it changes only if FIG adds an apparatus — but per-apparatus reporting is a
requirement, so an official must be able to rename or reorder them without a deploy.
Note the domain distinction: **a gymnast competes on four apparatus, chosen by level;
a judge is examined on all five.** What a gymnast performs is not what a judge is
tested on, so the exam's apparatus set does not follow the competition's.

**The set and its order, for seed data:** `Rope, Hoop, Ball, Clubs, Ribbon` — FIG
competition order, and the order the legacy database used. This is `Apparatus.position`
1 through 5. It carries no exam content and is safe to commit as a fixture.

**Apparatus and aspect are independent dimensions — a 4 × 5 grid**, and results are
read *both* ways. Down a row gives the aspect's component score, which is what
grades into a category. Across a column gives the candidate's marks for one
apparatus, which is what they actually want to see, exactly as a competition score
sheet works. **Apparatus is therefore a real field, never implied by position in a
list** — ordering is the thing that drifts.

Each score is entered against a timer; when it expires the candidate is moved on and
cannot go back.

Use the **current** FIG naming — `DA`, `DB`, `AV`, `EX` — not the old `D1+D2` /
`D3+D4` labels the legacy answer key carries (decided 2026-08-08).

So a candidate gives **20 marks**, each compared against that cell's own expert score
with `mark_numeric`. **That is where F5's magic number came from**: legacy summed 20
marks worth 5 each and called the total a percentage, which was only ever correct
because 5 apparatus × 4 aspects = exactly 20. Nothing in the code recorded that
dependency; a sixth apparatus would have scored everyone out of 125 while still
printing "%".

**Decided 2026-08-10: theory and practical are separate models.** The practical asks
nothing about the routine — the candidate watches and enters a number — so a practical
item has no stem blocks and no options, only a routine, an aspect and an expert score.
It shares nothing with a theory question but a position in a component. The spec's
original single `Question` with `marking_scheme: CHOICE | NUMERIC` has been revised;
the collapse-into-one-shape argument holds for the five theory *layouts*, not across
theory and practical. See the spec's Questions section.

**Decided 2026-08-08: a routine exists once and the four items reference it.**
The apparatus and its video belong to the routine; the aspect and the expert score
belong to the question. Four question rows each owning a copy of the same video is
the papers argument again — replace a video, miss one of the four copies, and a
candidate judges `EX` against last year's routine with no error anywhere. It also
matches the domain: a judge watches **one routine** and makes four judgements about
it. Note this is a **deviation from the spec**, which has `Question → QuestionBlock`
holding media and nothing in between; the exact shape is for the questions-app plan.

The four aspects stay **separate** — `DA` and `DB` are not averaged into one
Difficulty score. Each is `score_component` over its five videos, then `grade`
against the band set for its type. Note the two band sets differ: Excellent is 80%
for Difficulty but 90% for Artistry/Execution, which `grade(percentage, bands)`
already supports because bands are an argument.

**Decided 2026-08-08: `Difficulty = mean(DA, DB)` for the category rule, and it is
the mean of the two *rounded* aspect scores.** `DA` and `DB` stay separate for
scoring and reporting — a candidate sees both — but the category rule takes three
values, Difficulty, Artistry and Execution, which is why the spec's two worked
examples name Difficulty once.

**The rounding order is not cosmetic.** Rounding each aspect and then averaging is
not the same as averaging the raw values and rounding once: over a window 0.1 wide
on each axis there are 2,750 disagreements, and **1,020 of them change the Difficulty
grade** against the 80% floor. For example `DA 79.900`, `DB 80.085` gives `80.00`
Excellent one way and `79.99` Very Good the other — same twenty marks, different
category.

Take the mean of the rounded scores, for the same reason `grade` consumes a rounded
percentage: the candidate is shown `79.90` and `80.09`, and averaging those by hand
must reproduce the result. A number that cannot be recomputed from the figures on
the certificate is the one that loses an appeal.

**The examination produces a category, but does not award one** (established
2026-08-10 from General Judges' Rules §2.6; SAGF follows FIG). The awarded category
is capped afterwards by judging experience, by a first-cycle maximum of Category 3,
and by a limit of dropping at most two categories per cycle. **This system computes
the examination result and stops there.** That is the concrete reason the spec keeps
scoring and certification as separate events recorded against different people — the
information that caps the award is history the exam has never seen.

**The four grades then determine one overall category, and that piece is not built.**
`score_component` and `grade` get you to four grades; nothing turns four grades into
a category. From the two examples in the spec — Category 1 needs Difficulty
excellent with Artistry and Execution very good, Category 4 needs all at pass — the
rule looks like *the highest category whose per-aspect minimum grades are all met*,
which is the same lower-bound shape as `GradeBand.minimum` and the F9 level rule. The
weakest aspect caps the category. **The exact requirements per category are still
unknown** — see Open questions.

**Theory questions are banded by level, cumulatively.** A level 2 candidate sits
every level 1 question plus the level 2 additions; level 3 sits all three bands, and
so on. So a question carries the *lowest* level obliged to answer it, and selection
is `question.minimum_level <= candidate.level` — a lower-bound comparison, the same
shape as `GradeBand.minimum` and `floor_band_index`. Modelling it as
`question.level == candidate.level` looks reasonable and silently hands a level 3
candidate only the level 3 additions, sitting them a fraction of their exam. That is
exactly what the old app did — see **F9**.

**Decided 2026-08-05: a question exists once, and something else lists which
questions it contains.** Membership is explicit data — a many-to-many, not a scalar
`level` column and not a `minimum_level <= candidate.level` query. Overlap between
levels is the same question row referenced twice, never a copy of it.

Two things this buys, and both were argued rather than assumed. Duplicating a
question per level means an answer-key correction has to find every copy, and a
missed copy leaves two cohorts marked against different keys with no error anywhere
— F1's family. And a pure cumulative rule cannot express a level that *drops* or
replaces an inherited question; the first time the syllabus does that you bolt on an
exceptions table and arrive at the join table by a worse road.

"Cumulative" therefore describes how a question set is **built** — seed level 2 from
level 1, then add — not how it is queried. Note the usual reason to duplicate does
not apply here: keeping historical question sets stable is F1's snapshot's job, so
duplication buys nothing there.

**Refined 2026-08-08: the owner is `ExamComponent`. There is no separate `Paper`
model.** The spec already defines `ExamComponent` as "one per marked section of the
exam", carrying its own grade bands and its own marking table — which is exactly the
thing that should own a set of questions. Theory is one component holding choice
questions; the practical is four components holding five numeric questions each. A
level 2 theory component references the same question rows as level 1's, plus its
own additions. **One mechanism for both halves of the exam**, rather than papers for
theory and components for the practical.

The consequence for planning: **the questions app is content only** — `Question`,
`Routine`, `Apparatus`, blocks, media, admin, preview. Membership and selection live
with `ExamComponent` in the exams app, and **F9 moves to the exams/sittings plan
with them**, because F9 is about which questions a candidate is given, not about what
a question is.

**Absence is not a value — and the two-exam split is what enforces it.** Legacy
fabricated a practical answer of `"0"` for candidates who sat no practical, so a
component they never attempted scored roughly zero and was indistinguishable from
failing it (**F10**). With theory and practical as separate exams and separate
sittings, a candidate who did not sit the practical has no practical sitting at all,
and there is no field for a spurious zero to occupy.

Keep the principle anyway, because it recurs: this is the same distinction
`to_decimal` draws between a blank answer and an unreadable one (F3), and
`score_component([])` raising rather than returning `0` is the same guard inside the
scoring package. Any future code that aggregates across components must treat
absence as absence, never as a number.

## Read these before doing anything

- `docs/superpowers/specs/2026-07-28-rhythmic-exam-rebuild-design.md` — the design.
  Includes fifteen numbered findings (F1–F15) from the old app; each one is a bug the
  rebuild must fix, and several have tests written specifically to pin them. F1–F8
  came from the original audit; **F9 and F10 were found on 2026-08-05** while
  checking how legacy selected questions by level; **F11 and F12 on 2026-08-13** and
  **F13–F15 on 2026-08-15**, from old working databases rather than from the code.
  Assume there are more.
- `docs/superpowers/plans/2026-07-28-scoring-package.md` — the current plan.

## Layout

```
docs/superpowers/{specs,plans}/
rhythmic/     the new system. Paths in the plan are relative to HERE.
legacy/
  flask_backend/    the 2023 Flask app. Reference only. Do not modify or run.
```

`legacy/` is kept for exactly two things: the exam media (117 images, 10 videos)
and the type 1–5 templates to check new rendering against. **It gets deleted when
the media is migrated and the block renderers are built** — that condition was
agreed, so don't let tidiness pull the trigger early, and don't propose building on
it either.

The FastAPI backend was deleted on 2026-07-28 (recoverable from `4e6aa1b`,
`206ff42`). Don't suggest reviving it.

**Two old working SQLite databases, both untracked and covered by `.gitignore`'s
`*.db`. They hold the real question bank and the practical answer key, so neither may
ever be committed and their contents must not be quoted into commits, plans or chat.**
Aggregate shape — counts, distributions, column types, JSON key names — is safe, and is
where F9's confirmation and F11–F15 came from.

- **`rhytmic.db`**, produced 2026-08-13. 75 questions, all `question_type = 1`, none
  referencing media. A later, reduced state. Source of F11 and F12.
- **`rhytmic_master.db`**, found 2026-08-15. **The original bank: 89 questions across
  all five types, 85 theory and 4 practical.** Source of F13–F15. Predates the change
  that introduced levels, so it says nothing about F9.

**They are evidence of what was done, not a model for what to do.** Every structural
choice in them is one the rebuild is deliberately reversing: scalar `exam_level`,
positional `answer_1..answer_20` keys, `TEXT` expert scores, one result per person,
five private JSON schemas inside `VARCHAR` columns. Read them to find out what went
wrong, never to copy a shape.

**Two corrections the master database forced, both of which had reached this file as
fact.** The type 2–5 layouts were recorded as having no known data; they have data —
1 type 2, 2 type 3, 5 type 4, 39 type 5 — and their shapes are in F13. And the tracked
media in `legacy/` was recorded as unreferenced; the master database references 98
distinct files (88 `.jpg`, 10 `.mp4`) and **all 98 are present on disk**, across 44 of
the 89 questions. So the media migration has a manifest, and the images are provably
exam content rather than merely suspected of it — which raises, not lowers, the
priority of the exposure noted under Hard constraints.

Both corrections came from a claim in this file being checked rather than trusted.
Treat the rest of this section the same way.

## Spelling

The sport is *rhythmic*. The legacy tree and the old package spell it *rhytmic*.
The repo itself was renamed to `rhythmic_exam` on 2026-07-28. **New code uses the
correct spelling.** Don't "fix" the legacy tree, and don't propagate the typo into
new code.

## Hard constraints

- **No real exam content in this repository. It is public.** The question bank and
  answer key were removed on 2026-07-28. `legacy/flask_backend/doc/example_format.csv`
  is synthetic and safe. Before committing any data file, check whether it carries
  questions or answers. The 117 tracked exam images are a known pre-existing
  exposure, to be revisited at media migration.
- **`rhythmic/scoring/` imports nothing from Django and touches no database.** If a
  module there needs a framework, the boundary is wrong. Enforced by ruff `TID251`,
  which bans `django`, `sqlalchemy` and `flask` — see Tooling below.
- **`Decimal` everywhere for marks and deductions, never `float`. Never compare
  answers as strings** — finding F3 is exactly that bug.
- **Marking tables and grade bands are data, never literals in Python.** FIG
  republishes them every four-year cycle and doesn't finalise them until after the
  first exam is sat.
- **Check `git status` before committing.** `git commit` commits the whole index —
  this already caused a file to be committed after Altus had declined it.

## Commit messages

Conventional Commits, **starting with the first commit after `c0839c5`**. Everything
up to and including `c0839c5` predates the convention — do not rewrite those messages
to match.

```
<type>(<scope>): <imperative subject>
```

- **Types, closed set:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.
  Nothing else. An unbounded type list is the same as no convention.
- **Scope** is the package or Django app: `scoring`, `questions`, `exams`,
  `accounts`, `frontend`, `docs`. Omit only when the change is genuinely repo-wide.
- **Subject:** imperative mood ("add", not "added"/"adds"), lower case after the
  colon, no trailing full stop, under ~72 characters.
- **Tests ship with the behaviour they cover**, so they are part of it —
  `feat(scoring):`, not `test:`. Reserve `test:` for tests added to code that
  already exists, which is mostly the F6 backfill.
- **The prefix does not excuse a vague subject.** `chore: project setup` is a bad
  message with a prefix on it. Say what changed.
- **Body explains why**, not what — the diff already says what. Wrap at 72.
- **When handing him a commit, say what the body should carry *before* giving the
  command, and give bare `git commit` rather than `git commit -m`.** `-m` commits on
  the spot, so body guidance that follows it arrives after the commit exists and
  costs a rebase — this happened on 2026-08-10. Reserve `-m` for commits that need no
  body at all, such as a pure formatting chore.
- **Cite the finding** when a commit fixes one: `fix(scoring): compare answers as
  Decimal, not string (F3)`. The findings are the spine of the rebuild and the log
  should be searchable by them.

No release automation is wired up and none is planned; the prefixes are for humans
reading the log. There is no `commit-msg` hook — **this convention is held by
discipline alone.** The `pre-commit` hook added on 2026-08-04 enforces ruff, and
says nothing whatever about commit messages; don't mistake one for the other.

## Current state

**Two plans finished: the scoring package (seven tasks) and the Django skeleton
(five). The questions app is in progress — Tasks 1-7 of nine are done.** As of
2026-08-22, **125 tests pass** and both `ruff check .` and `ruff format --check .`
are clean. Run all three from `rhythmic/`.

| file | tests |
|---|---|
| `test_aggregate.py` | 18 |
| `test_values.py` | 17 |
| `test_tables.py` | 14 |
| `test_marking.py` | 12 |
| `test_public_api.py` | 10 |
| `test_questions_admin.py` | 10 |
| `test_questions_blocks.py` | 10 |
| `test_questions_practical.py` | 10 |
| `test_legacy_parity.py` | 9 |
| `test_questions_theory.py` | 7 |
| `test_questions_history.py` | 5 |
| `test_django_smoke.py` | 2 |
| `test_smoke.py` | 1 |

**Postgres must be running for the full suite to pass.** `docker compose up -d` from
the repository root. `test_django_smoke.py::test_database_is_reachable` needs it, and
so does every `@pytest.mark.django_db` test in the questions app; the 82 scoring
tests do not.

**The plan's own test-count estimates are stale** — it predicts 54 by Task 6. Tasks
4 and 5 both grew cases beyond its table. Don't chase the plan's numbers; they were
written before the tests were.

- `c0839c5` — package skeleton, editable install, smoke test.
- `58e94d8` — `scoring/values.py`, fixes F3. `to_decimal` returns `None` for blank,
  whitespace-only and `None`; raises `UnparseableAnswer` for garbage **and** for
  non-finite values (`nan`, `Infinity`, which `Decimal` otherwise accepts happily).
  A blank is the candidate's own choice; unreadable input is a fault someone must
  see. Conflating them hides data errors in results.
- `b3bb4f2` — ruff.
- `83a1661` — `scoring/types.py` and `scoring/tables.py`, fixes F4. `BandRow` and
  `MarkingTable` are frozen dataclasses; `MarkingTable.lookup` is **keyword-only**,
  because both arguments are `Decimal` and a positional swap returns a plausible
  wrong percentage instead of an error. Both dimensions floor into half-open bands
  via one shared helper, `tables.floor_band_index`, which walks bounds from the top
  down — so the open-ended top band and the below-the-bottom fallback need no
  special case, and rows and columns cannot drift apart.

  `MarkingTable.__post_init__` rejects malformed tables at construction, so no
  invalid table can reach `lookup` by any path. It went beyond the plan: validating
  in `lookup` would re-answer, on every call, a question the `frozen=True` settles
  at `__init__`. Ordering is the check that matters — unsorted bounds return a real
  index and a wrong mark, where every other violation raises `IndexError`.

- `6a6b495`, `d44f694`, `89cb840` — `pytest-cov` in the `dev` extra, a `ruff format`
  fix `83a1661` should have carried, and the test coverage flagged as missing: the
  below-every-bound fallback in `floor_band_index`. That test needs its own table
  whose lowest bounds are above zero, because the shared fixture starts at `0.0` and
  cannot reach the branch. It guards a real regression — rewriting the walk as
  `bisect_right(bounds, value) - 1` returns `-1`, which indexes from the end and
  awards the *top* band to a candidate who scored below the bottom one. Verified by
  mutation, not by argument.

- `b47f480` — `scoring/marking.py`, Task 4. `mark_numeric` stays thin: `to_decimal`,
  one subtraction, `abs()`, `lookup`. Every band decision lives in `tables.py` and
  every parsing decision in `values.py`; that single subtraction is the only
  arithmetic that is marking's own business. A blank answer marks zero;
  `UnparseableAnswer` propagates rather than being caught and re-raised. Note that
  `mark_choice` has no source in the FIG rules — see Open questions.

- `f0cbc33` — `scoring/aggregate.py` plus `GradeBand`, fixes F5. Legacy summed
  per-item marks and called the total a percentage, which was correct only for
  exactly 20 items worth 5 marks each; 21 items reports 105%. `score_component` is
  the arithmetic mean, quantized to 2dp with `ROUND_HALF_UP`.

  **The rounding decision, which is the one that reaches candidates.** `grade`
  consumes the *rounded* value, so the number shown is the number that decided the
  grade, and a tie at a band floor resolves in the candidate's favour — `49.99` and
  `50.00` average to `49.995`, round to `50.00`, and pass. Grading an unrounded
  value was never available: `Decimal` division already rounds to
  `getcontext().prec`, so the real choice was 2dp deliberately or 28 significant
  digits by accident. `ROUND_HALF_UP` versus `ROUND_HALF_EVEN` cannot change a grade
  against *integer* band floors — reaching one at 2dp needs `X.995`, whose preceding
  digit is 9 and therefore odd, so half-even rounds up too — but it is pinned by a
  test regardless, because the displayed number is what a candidate re-checks by
  hand, and because FIG may publish a non-integer floor.

  `grade` selects the bands the percentage meets and takes the highest minimum,
  rather than walking a sorted list. Band ordering therefore carries no meaning and
  the loader owes no sort contract. This holds only while the minimums are distinct
  — `max` breaks ties by input order. If a `GradeScale` type ever wraps the bands,
  distinctness and sortedness are what it should validate.

- `ce6e7bd`, `9486400`, `1b5da96` — the pre-commit hook, its documentation, and the
  root `ruff.toml` guard. See Tooling.

- `a77df3b` — `scoring/__init__.py`, Task 6. Nine names re-exported with `__all__`
  asserted for **exact** equality, so a leaked name fails when it is introduced
  rather than after something imports it. Callers write `from scoring import
  mark_numeric`, never `from scoring.marking import ...`, which is what keeps
  internal modules movable. The test looks names up with `hasattr` against a list of
  strings; importing them at the top of the test module would turn a red into a
  collection error that takes the whole suite down.

- `c54d8c5` — `scoring/legacy.py` and `tests/test_legacy_parity.py`, Task 7.
  `sagf_legacy_table()` states the old SAGF scheme — 5 marks for an exact match,
  0.25 fewer per 0.05 of difference, zero at 1.00 — as a single-row `MarkingTable`
  of 21 columns. Bounds are generated with `Decimal(i) * Decimal("0.05")`, never
  `Decimal(i * 0.05)`, which multiplies in float first and puts the `0.15` bound at
  `0.15000000000000002` — dropping a candidate sitting exactly on that boundary
  into the band below.

  **The parity sweep is the deliverable, and it lives in the commit body.** Across
  every difference from 0.00 to 1.50, old and new agree on all 70 cases where the
  legacy code returned anything at all, bar one. Three divergences, all deliberate:
  F3 (`"0.3"` against expert `0.30` scored 0, now 100), F4 (**80 of the 99**
  differences that reached `diff_arr.index()` raised `ValueError`, now they floor
  into a band), and difference `0.45`, where legacy's float marks returned
  `55.00000000000001` — not a numbered finding, pinned by a test so a later sweep
  reads it as legacy's bug rather than a regression here.

  **Parity needed no real exam content.** An earlier note in this file claimed the
  data question had to be settled first; it was wrong. The comparison runs on
  synthetic difference values, not candidate answers. The legacy function was
  copied verbatim into a scratch script rather than imported, so nothing under
  `legacy/` was run — do the same for any future parity work.

### The Django skeleton, 2026-08-08

Plan: `docs/superpowers/plans/2026-08-05-django-skeleton.md`. Five tasks, all done.
`13262c1`, `5773a44`, `43092ff`, `5da607e`, `37500f1`.

- **The framework ban moved to `rhythmic/scoring/ruff.toml`.** It had been in
  `rhythmic/pyproject.toml`, so it applied to *everything* under `rhythmic/` despite
  its message naming `scoring/` — the first Django file would have been blocked by
  the pre-commit hook. `extend = "../pyproject.toml"` keeps the parent rule set;
  without it `scoring/` would silently drop to ruff's defaults and lose `RET` and
  `BLE`. Verified both directions, because the failure mode is a ban that stops
  firing while everything still looks green.

- **`config/` is the Django project; Django is a `web` extra, not a dependency.**
  `[tool.setuptools] packages = ["scoring"]` still declares only the scoring package,
  so `config/` is outside the `rhythmic-scoring` distribution entirely. Install with
  `pip install -e "rhythmic[dev,web]"`.

- **One `.env` and one `.env.example`, both at the repository root.** Compose reads
  `.env` from its own directory; Django reaches up with
  `load_dotenv(BASE_DIR.parent / ".env")`. Two copies of the same Postgres password
  is a bug waiting to happen.

- **`SECRET_KEY` and the Postgres credentials use `os.environ[...]`; `DEBUG`,
  `ALLOWED_HOSTS`, `POSTGRES_HOST` and `POSTGRES_PORT` use `.get` with defaults.**
  The asymmetry is deliberate: a missing secret must halt, because a fallback would
  sign every session cookie with a readable value. `DEBUG` defaults to **false** so
  forgetting it fails closed. Verified by hiding `.env` and confirming a `KeyError`
  and a non-zero exit — not a working site. No generated key ever reached a commit.

- **`compose.yaml` runs Postgres only** — not the application, deviating from the
  spec's Operations section deliberately. Containerising an app with no views means
  a Dockerfile and a WSGI server for nothing; it belongs with the first thing worth
  deploying.

- **`postgres:17`, not `postgres:17-alpine`.** Alpine ships musl, which has no real
  locale support, so the cluster initialises with C collation — byte order. The same
  seven names sort `Ácker äpple Botha de Beer van der Merwe Van Wyk Zulu` on Debian
  and `Botha Van Wyk Zulu de Beer van der Merwe Ácker äpple` on Alpine. Afrikaans
  surnames with lowercase particles and any accented name sort wrongly, and a
  `UNIQUE` index built under one collation is invalid under the other. Verified by
  running both images.

- **Port binding is `"127.0.0.1:${POSTGRES_PORT}:5432"`.** Docker publishes ports by
  writing firewall rules, so an unrestricted binding is reachable from the network.
  **This regressed twice in one session**, the second time via a `POSTGRESS_HOST`
  typo: Compose substitutes a *blank string* for an unset variable and only warns,
  and a blank host means all interfaces. Any Compose warning about an unset variable
  means something is being substituted with nothing — check `docker compose ps` for
  `0.0.0.0`.

  The same mechanism bites `.env` values: a Django `SECRET_KEY` containing `$cat`
  made Compose warn and truncate. **Single-quote values in `.env`** — verified that
  Compose then treats them literally and `python-dotenv` still strips the quotes.
  Regenerating the key is not a fix: 42% of generated keys contain a `$` followed by
  a letter.

- **`pytest-django`, one runner.** `DJANGO_SETTINGS_MODULE` and `pythonpath = ["."]`
  live in `[tool.pytest.ini_options]`. `pythonpath` is required because the editable
  install declares only `scoring`, so `config` is otherwise unimportable — and the
  failure is a collection error that takes the whole suite down. Unmarked tests are
  *blocked* from database access, which is what keeps the 81 scoring tests honest
  about needing no database.

  `pytest-django` supplies a `client` fixture. It was not obvious that it did, and
  a hand-rolled one silently shadowed it — say when a fixture comes from a plugin
  rather than assuming it is known.

**`ruff check` and `ruff format` are separate commands** — a clean `check` says
nothing about formatting. That gap cost review rounds on Tasks 3 and 5, which is
why the pre-commit hook exists.

**The questions-app plan is written** — `docs/superpowers/plans/2026-08-10-questions-app.md`,
nine tasks. It is **content only**: `Question`, `Routine`, `Apparatus`, the content
blocks replacing the legacy type 1–5 shapes, media upload, admin, and a preview
action. It knows nothing about levels, exams or who sits what.

**Next action: Task 8, the preview.** Task 9 was added on 2026-08-22 and is the
test backfill the mutation sweep found — do it after Task 8, not instead of it.

**`rhythmic/tools/mutation_sweep.py` exists and should be run at the end of every
task from now on.** It breaks one claim at a time and checks that a test objects; a
SURVIVED mutant is a change to the code nobody noticed. Run from `rhythmic/`:

```bash
../.venv/bin/python tools/mutation_sweep.py
```

First run against the finished questions app, 2026-08-22: **20 mutants, 11 killed,
9 survived.** The survivors are `Routine` and `Question` ordering,
`ContentBlock.__str__`, `list_select_related`, `SimpleHistoryAdmin`, history on
`Question`/`Option`/`OptionBlock`, and `list_filter` on aspect. All but the last are
Task 9.

**The sweep cannot reach the schema, and that is a finding in itself.** The test
database is built from `questions/migrations/`, not from `models.py`, so renaming
`uq_one_correct_option_per_question` in the model passes the whole suite. Every
constraint test in this project therefore tests the *migration*, and is only as
trustworthy as someone having remembered to run `makemigrations`. There is no
`makemigrations --check` test yet; Task 9 adds it, and it is what makes the rest
mean what they appear to mean.

New mutants belong in the catalogue as behaviour is added — the file is a record of
what the code claims, which is why it is worth keeping rather than being a one-off
script.

- `d035ce8` — Task 1. The `questions` app, registered in `INSTALLED_APPS`.
- `a472415` — Task 2. `Apparatus` and `Routine`, `MEDIA_ROOT`/`MEDIA_URL`, media
  served under `DEBUG`, `rhythmic/media/` gitignored.

  **Two review findings worth carrying forward.** `Routine.Meta.ordering` names
  `apparatus__position` rather than `apparatus`. Both generate identical SQL today —
  Django follows a bare FK to the related model's own `Meta.ordering` and falls back
  to its primary key when there is none — so this is taste, but it survives someone
  deleting `Apparatus.Meta.ordering`, which the implicit form does not.

  The ordering *test* was the real finding, and it is general. As first written it
  called `Apparatus.objects.all().order_by("position")` — supplying the very sort it
  existed to check, so it passed with `Meta.ordering` deleted. Confirmed by mutating
  `Apparatus._meta.ordering` to `[]` in a shell and printing the query: the model's
  `ORDER BY` disappears while the test's does not. **A test that specifies the
  behaviour it is checking tests the ORM, not the model.** Assert on the bare
  queryset.

  Also: test videos are set with a plain string, `video="routines/example.mp4"`, not
  `SimpleUploadedFile` — the latter writes real files into `rhythmic/media/` through
  `.create()` on every run. The plan recommended it and was wrong; corrected in
  `042364b`.

- `f633dec` — Task 3. `PracticalItem(routine, aspect, expert_score)` and the `Aspect`
  `TextChoices`. `aspect` carries **no default** and `expert_score` is
  `DecimalField(max_digits=4, decimal_places=2)`; the `UniqueConstraint` on
  `(routine, aspect)` is a real `UNIQUE` index. Reasoning is in the commit body.

  **`sqlmigrate` is how you check a model reached the database as intended** —
  `manage.py sqlmigrate questions 0002` renders the DDL without running it. It showed
  `numeric(4, 2)` rather than `double precision`, the named `UNIQUE (routine_id,
  aspect)`, and `varchar(2) NOT NULL` with no `DEFAULT`. Note also that Django's
  migration optimizer folds `AddConstraint` into `CreateModel` when both are in the
  same migration, so a missing `AddConstraint` operation is not a missing constraint —
  a review comment of Claude's said otherwise and was wrong.

  **Third instance of the same test defect: the test supplied the behaviour it was
  checking.** `test_expert_score_is_stored_as_decimal` asserted `isinstance(...,
  Decimal)` on the object `create()` returned, which is the literal that went in, so
  it passed without Postgres being involved and would pass against a `FloatField`.
  `create()` hands back `9.5` where a reload gives `Decimal('9.50')` — the conversion
  is the database's, and only a reload sees it. Same shape as Task 2's `.order_by()`.
  **Reload with `objects.get(pk=...)` before asserting anything about storage.**

  A `related_name` reverse accessor (`routine.items`) draws a red squiggle in the
  editor and works fine — Django builds it at class-preparation time, so Pylance
  cannot see it. `django-stubs` is the fix if it becomes annoying; it is not
  installed.

- `af153e2` — Task 4. `Question` and `Option`. `CASCADE` here against `PROTECT` in
  Tasks 2 and 3: an option has no meaning without its question, where an apparatus
  outlives the routines referencing it. The partial unique index —
  `UniqueConstraint(fields=["question"], condition=Q(is_correct=True))` — gives **at
  most one** correct option, never **at least one**; a question with zero correct
  options still saves, because the database has nothing to check until the child rows
  exist. Task 7's formset validation closes that, and
  `test_a_question_with_no_correct_option_still_saves` is the marker.

- `a8915b0` — Task 5, fixes F13. `Kind`, abstract `ContentBlock`, `QuestionBlock` and
  `OptionBlock`. Legacy's five per-type JSON schemas become rows: a text-plus-image
  stem is two blocks, and image options are `kind=IMAGE` rather than a distinct
  question type. Reasoning is in the commit body.

  **The kind `CheckConstraint` is declared once on the abstract base and templated
  with `%(app_label)s_%(class)s_`**, so each child gets its own copy under its own
  name — constraint names are database-wide, so an untemplated name fails at
  `migrate`. A child must write `class Meta(ContentBlock.Meta)` **and**
  `constraints = ContentBlock.Meta.constraints + [...]`: assigning a fresh list
  replaces the inherited one. Verified that a bare `class Meta:` in a child yields
  `ordering=[]` while inheriting or omitting `Meta` yields `['position']` — so the
  bare form silently drops both. `test_the_kind_constraint_applies_to_the_option_block_too`
  exists because only a test on the *second* child can see that.

  **Deferred constraints are invisible to `pytest-django`.** The `(parent, position)`
  uniques are `DEFERRABLE INITIALLY DEFERRED` so that code rewriting positions inside
  one transaction can swap two of them. Postgres then checks them at `COMMIT`, and
  `django_db` rolls back instead of committing — so two rows sharing a position insert
  cleanly and the `IntegrityError` surfaces in *teardown*, reported as an ERROR
  against a fixture on a test that "passed". A `pytest.raises` around the duplicate
  therefore passes whether the constraint exists or not. The tests force it with
  `SET CONSTRAINTS ALL IMMEDIATE` in a fixture. `CHECK` constraints are unaffected —
  they fire on every row write.

  The fixture takes `db` **for documentation, not because it breaks without it** —
  verified that it works either way, since pytest-django's `_django_db_marker` is
  autouse and autouse fixtures run first at the same scope.

  **Isolate the row you are testing, because the error message cannot.** One
  constraint with three OR'd arms produces one message for every violation, so
  `match=` cannot tell you which arm fired. `kind=IMAGE` with text and *no image*
  breaks two clauses at once and still passes with the text clause deleted from the
  constraint; `kind=IMAGE` with a valid image *and* text is the isolated case.
  Confirmed by rewriting the constraint in Postgres inside a test transaction —
  DDL is transactional there, so the weakened version rolls back.

  Match on the **constraint name only**, never Postgres's full sentence: the wording
  belongs to Postgres and will change.

  **Fourth instance of the test supplying its own behaviour**, after Task 2's
  `.order_by()`, Task 3's `isinstance` on what `create()` returned, and an interim
  `first()` here: `assert block1.position == block2.position` compares two literals
  the test had just passed to `create()`, so it holds under every mutation including
  deleting the model. Replaced with `list(question.blocks.all()) == [block]` per
  parent, which reads from Postgres. Related mechanic worth knowing —
  `QuerySet.first()` silently applies `order_by("pk")` when the queryset is
  unordered, so it never raises on an unordered queryset, it just picks for you.

- `ddbd625` — Task 6. `django-simple-history` on `Question`, `Option`,
  `PracticalItem`, `QuestionBlock` and `OptionBlock`. Not on `Apparatus` or
  `Routine` — "who renamed Ribbon" is not dispute material, and every historical
  model doubles the writes on its table.

  **The plan named only the first three and was wrong.** It was written before Task
  5, and after Task 5 every word a candidate reads lives in a block row: history on
  `Question` and `Option` alone records who flipped `is_correct` and nothing about
  who reworded a distractor. Corrected in the plan.

  **History is not F1's fix.** F1 is results being recomputed against the live
  answer key; it is closed by the sitting freezing its own snapshot of marks, in the
  exams app. History answers a different question — *who changed this key, and when*
  — which is why the spec rejected version chains rather than adding them. A commit
  body claiming `Fixes F1` here was caught at review.

  **`simple_history` is an app *and* a middleware, and they do different jobs.** The
  middleware records *who*, from `request.user`, so it must sit after
  `AuthenticationMiddleware`; without it history records what changed and not who.
  `INSTALLED_APPS` gets the templates, template tags, management commands and
  translations — the package ships **no `migrations/`**, because each historical
  model is built under the tracked model's own app (`models.py:302`,
  `app_module = "%s.models" % model._meta.app_label`). So the tables land in
  `questions/migrations/` and the recording half works even unregistered — which is
  why the omission survives until someone clicks History in the admin.

  **The audit outlives the record.** simple_history drops the `FOREIGN KEY` on the
  tracked relation: `questions_historicalquestionblock.question_id` is a plain
  nullable `bigint` with an index and no constraint. `Question.delete()` cascades the
  live block away and leaves its history standing, plus a `-` row marking when it
  stopped existing. Historical tables also do **not** carry the model's own
  `CheckConstraint` — correct for an append-only log, which must be able to hold
  states you would now reject.

  **Historical querysets order newest-first** — `("-history_date", "-history_id")`,
  from the package source. So `history.first()` is the latest edit and
  `history.last()` is the creation, the opposite of every other queryset in the
  suite.

  **Fifth instance of a test that cannot fail.** `test_apparatus_has_no_history` was
  written as `pytest.raises(Exception): Apparatus._meta.get_field("history")` —
  but `HistoricalRecords` installs a **manager, not a field**, so `get_field` raises
  `FieldDoesNotExist` on every model in the project, `Question` included. Verified
  both ways. `hasattr(Model, "history")` is the probe that discriminates.

  **`bulk_create()` and `queryset.update()` bypass the signals and write no
  history** — the package ships `bulk_create_with_history()` and
  `bulk_update_with_history()` for that. Same list as the `clean()` argument: shell,
  management commands, bulk operations, raw SQL. Relevant to the media migration.

- `3d8f554` — Task 7, the admin. All five models registered; `QuestionBlock` and
  `Option` inline under `Question`, `OptionBlock` under `Option`. Reasoning is in the
  commit body.

  **`admin.py` is discovered by name.** `AdminConfig.ready()` calls `autodiscover()`
  (`django/contrib/admin/apps.py:27`), which imports the `admin` submodule of every
  installed app. That import *is* the registration; rename the file and every screen
  silently disappears. An inline is never registered — `@admin.register` only writes
  into `admin.site._registry`, and a registry entry is what creates URLs.

  **A green `manage.py check` is only evidence about what the checker reached.**
  `QuestionAdmin` was written with `list_display = ("reference", "created_at",
  "updated_at")` against a model with no timestamp fields, and checks passed — because
  the class carried no `@admin.register`, so `admin.E1xx` never looked at it.
  Registering it in a shell produced four errors immediately. Same shape as the test
  defect this project keeps producing: a validator with nothing registered validates
  nothing.

  **`SimpleHistoryAdmin`, not `ModelAdmin`, on the three tracked models.** Plain
  `ModelAdmin` already has a History button (`django/contrib/admin/options.py:2561`)
  — it lists `LogEntry` rows, which record admin actions only and as free text.
  `SimpleHistoryAdmin` replaces that view with the historical rows, so Task 6's
  history became *readable* here rather than merely recorded. Verified: the history
  page renders both the old and the new expert score.

  **`list_select_related` on `PracticalItemAdmin`, and the trap is `__str__`.** The
  changelist applies `select_related()` on its own when `list_display` names a
  `ForeignKey` (`django/contrib/admin/views/main.py:531`), but only one hop.
  `Routine.__str__` reaches through to `apparatus.name`, so a 20-row key — the real
  size — cost 25 queries. With `["routine__apparatus"]`, 5. **A `__str__` that
  crosses a relation is a query per row and is invisible until counted.**

  **`simple_history.register()` is the model-layer alternative to
  `HistoricalRecords()`, not an admin thing.** Calling it in a `ModelAdmin` body runs
  at import time and raises `MultipleRegistrationsError`, which fails
  `autodiscover_modules` and takes the whole project down.

  **The deferrable constraints do not do what this file said they did.** Task 5
  recorded that the `(parent, position)` uniques are `DEFERRABLE` "so an admin reorder
  can rewrite positions inside one transaction". Disproven 2026-08-22: posting a swap
  through the admin is rejected by `ModelForm._post_clean()`, which runs
  `validate_unique()` — a `SELECT` for a conflicting row — *before* any `UPDATE` is
  emitted, so deferral never comes into it. Below the form layer it works exactly as
  designed: the same swap in one transaction succeeds for `QuestionBlock` and fails
  for `Option`, whose constraint is immediate. **Deferral is necessary for an admin
  reorder but not sufficient**; a custom formset renumbering from form order is the
  missing half, and is not built. Consequence: `Option`'s constraint stays immediate
  and `test_duplicate_position_for_the_same_question_is_refused` is not at risk.

  **`OptionInlineFormSet` enforces exactly one correct option, not at least one.**
  The plan said at-least-one and was wrong: two correct options hits
  `uq_one_correct_option_per_question` as an unhandled `IntegrityError` — a 500 page
  rather than a form error. Form layer only, so a shell, a management command or a
  fixture load still bypasses it.

  **Iterate `self.forms`, not `self.cleaned_data`.** The latter is a property that
  calls `self.is_valid()` and raises `AttributeError` when any child form failed
  (`django/forms/formsets.py:277`), so one bad `position` blows up inside `clean()`.
  Django's docs work around it with `if any(self.errors): return`; iterating
  `self.forms` needs no guard. Advice in this file and the plan said otherwise.

  **Sixth, seventh and eighth instances of a test that cannot fail**, all in one task.
  (6) `assert "Questions" in body` — page chrome, true on a changelist showing
  `0 questions`, and the row it was supposed to prove was never created because the
  setup POSTed the add form instead of using `objects.create`. (7)
  `assert item.aspect in body` where `aspect` is `"DA"` — present with zero rows,
  because `list_filter` renders `?aspect__exact=DA` in the sidebar. The obvious fix,
  asserting the display label, is the same bug: that is the sidebar's link text. (8)
  Two admin POST tests whose inline prefixes were `optionblock_set-` rather than
  `options-` and `blocks-`; **deleting every `is_correct` key from the payload changed
  nothing**, because an unbound formset has zero correct options and `clean()` raises
  the same message. Both passed for two review rounds.

  **The inline prefix is the FK's `related_name`** —
  `BaseInlineFormSet.get_default_prefix()` returns the accessor name
  (`django/forms/models.py:1174`). `<model>_set` is the no-`related_name` default.
  Every inline on the page needs its four management keys or the formset never binds
  and the response carries `ManagementForm data is missing`. **A `200` from an admin
  POST means the form re-rendered — it failed;** a save is a `302`.

  **Write the control test first.** `test_a_question_with_one_correct_option_saves_successfully`
  is what proves the payload is well-formed, and it is why the two rejection tests can
  be believed. Verified by mutation: with the `!= 1` check replaced by `if False:`,
  both rejection tests fail and the control still passes.

  **A paused VS Code debugger holds the test database open.** pytest-django then
  cannot drop and recreate `test_rhythmic` — Postgres reports "database is being
  accessed by other users" and the run dies with `SystemExit: 2` before collection.
  The message names a database problem; the cause is a breakpoint.

**F9 and F10 both land in the exams/sittings plan**, along with `ExamComponent`,
membership, sittings and the freeze. Then accounts and the roster, then the React
island last.

Write the plan before writing code; that ordering is what the whole rebuild has run
on. The spec's Questions section already specifies `Question`, `QuestionBlock`,
`Option` and `OptionBlock` in detail, so this is planning work rather than design
work — with one deviation to design deliberately: `Routine` and `Apparatus` are not
in the spec, and they exist so that one video is referenced by four questions instead
of copied into each.

Each task in a plan ends at a **review gate**. He posts the code; you review it
before he starts the next task.

### Environment

The root `.venv` is the one in use, and it is now clean — Flask and SQLAlchemy are
gone, so `import flask` fails inside `scoring/` as intended. Earlier advice to build
a separate venv for `rhythmic/` is moot; don't repeat it. `rhythmic-scoring` is
installed editable, with pytest and ruff from the `dev` extra.

### Tooling

Ruff lints and formats, configured in `rhythmic/pyproject.toml`. The rule set is
chosen, not defaulted: `E W F I UP C4 B TID RET BLE SIM`, with `E501` ignored
because the formatter owns line length. `RET` and `BLE` are in because both caught
real bugs in `values.py`; ruff's stock selection would have caught neither.

**Run ruff from `rhythmic/`.** That is where the rule set lives and where the hook
runs it.

The root `ruff.toml` added on 2026-08-05 is a **guard, not a rule set** — one
`extend-exclude = ["legacy"]` line. Before it existed there was no config at the
root, so a run started there fell back to ruff's defaults and walked `legacy/`;
a stray `ruff check --fix` rewrote 25 reference files, reordering imports and
converting `.format()` calls to f-strings, `exam_utils.py` among them. Recovered
with `git restore legacy/`, since the tree was committed.

Ruff resolves the nearest config per file, so `rhythmic/` lints under its own
selection regardless of where you invoke from — the root file changes what ruff
is *allowed to reach*, never how it judges anything.

`ruff check --fix` is not safe to run blind. It once offered to delete the only
import in the smoke test, which would have left a test that passes even when the
package is broken. Read the findings before fixing.

**Formatting is enforced by a pre-commit hook**, `.githooks/pre-commit`, added on
2026-08-04 after `ruff format` was forgotten before a commit twice — once on Task 3
(`d44f694`) and once on Task 5. It runs `ruff format --check` and `ruff check` from
`rhythmic/` on the `.py` files **staged for that commit**, reports both before
aborting, and blocks rather than reformatting: a hook that edits your index puts
content in the commit you never read.

- It is **not** picked up by a fresh clone. `core.hooksPath` is local config, so
  each clone needs `git config core.hooksPath .githooks` once.
- Unstaged work in progress does not block a commit — only staged files are checked.
- It deliberately does **not** run pytest. A slow hook is a hook that gets
  `--no-verify`'d. Tests stay a separate gate.
- **It checks the staged blob, not the working-tree file** (fixed 2026-08-10). It
  reads each file with `git show ":path"` and pipes it to ruff with
  `--stdin-filename`, so what is checked is exactly what is committed, and per-file
  config resolution still applies — `scoring/` still gets its framework ban.

  It did check working-tree files until 2026-08-10, and that let a real defect
  through: `git add` a dirty file, `ruff format` the working tree, `git commit`, and
  the hook sees a clean tree while git commits the dirty blob. That is how the
  whitespace in `37500f1` was committed. `git stash --keep-index` would also have
  fixed it and was rejected — a hook that stashes can lose work if it exits badly.

  **Consequence when it blocks you: re-stage.** Fixing the file on disk changes
  nothing until `git add` puts the fix in the index.

## Open questions, none blocking

1. **Partly resolved 2026-08-08.** Naming follows the **current** cycle — `DA`,
   `DB`, `AV`, `EX` — not the legacy answer key's `D1+D2` / `D3+D4`. What is still
   open is the *table data*: which marking table and which band boundaries SAGF
   actually publishes. Affects data loaded at runtime, not the design.
2. Candidates per sitting. Assumed tens.
3. **Resolved 2026-08-05.** `mark_choice` is an SAGF national addition, not a FIG
   one. **Superseded 2026-08-08:** theory is no longer a real certification
   component at all — see What this is.
4. **Resolved 2026-08-08.** Theory and practical are never combined. Two separate
   results. Legacy's `main/routes.py:453-460` carried them side by side with no
   average or combined grade anywhere, which was right.
5. **Resolved 2026-08-10.** The table is **§2.6 of the General Judges' Rules**, not
   table 2.4 of the RG-specific ones, and **SAGF follows FIG**. Full table and the
   experience caps are in the spec. The inferred rule held: highest category whose
   three minimums are all met, weakest aspect capping. Note Category 1 is the only
   asymmetric row, and that **the examination result is an upper bound on the award,
   not the award itself** — judging experience, a first-cycle cap and a two-category
   drop limit all apply afterwards.
6. **Resolved 2026-08-08.** "Difficulty" in the category rule is `mean(DA, DB)` —
   the mean of the two rounded aspect scores — not a requirement that both reach the
   grade independently. See What this is for the rounding-order argument.
