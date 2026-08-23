# Decisions log — finished plans

Moved out of `CLAUDE.md` on 2026-08-23 to keep it under the always-loaded memory
budget. These two plans are **complete**; nothing here is pending work. Read it when
you touch the code it describes — the reasoning is not reconstructable from the diffs.

## The scoring package, seven tasks

Plan: `docs/superpowers/plans/2026-07-28-scoring-package.md`.

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
