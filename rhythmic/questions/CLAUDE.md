# Questions app — working notes

## Known limitation: authoring an option takes five saves

**Django's admin does not nest inlines two levels deep**, and an option's text lives
in an `OptionBlock`. So the Question page offers `QuestionBlock` and `Option` inlines
— siblings, both children of `Question` — and an option's *text* is not reachable
from it. Confirmed by inspecting the registry: `Question` carries
`['QuestionBlock', 'Option']`, `Option` carries `['OptionBlock']`, and `OptionBlock`
is not reachable from the Question page at all.

Authoring one four-option question is therefore: create the options on the Question
page (`position` and `is_correct` only), save, then open each Option separately and
add its block. Five saves, four of them on pages the author has to know exist. Found
2026-08-24 with eight real options in the dev database holding zero blocks and
rendering as four empty `<li>` elements.

**This weakens a claim the questions-app plan made** — that bulk import was
unnecessary "because the admin is the authoring surface". It is the authoring
surface; it is a slow one.

**Not fixed, deliberately.** There is no question bank to enter yet, and the right
shape depends on how many options are images rather than text — which the media
migration will answer. Three routes when it matters: accept it; add a `text` field to
`OptionInline` that writes an `OptionBlock` in `save_related`, which covers text-only
options and still sends image options to the second page; or take
`django-nested-admin`, which is a dependency that overrides a lot of admin internals.

**A related trap for whoever hits this next.** `QuestionBlock` is *not* a question —
the blocks of a `Question` are the parts of one stem, assembled in `position` order,
and the options belong to the question as a whole. Two questions means two `Question`
rows. A stem of two paragraphs renders its options after the second one, which reads
like the options attached themselves to the wrong block.

