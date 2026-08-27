# Eval set and harness

20 scored plan packages, 4 unscored calibration packages from the
class activity, instructor gold labels, and a runnable harness that
grades any rubric-plus-evidence-guide-plus-procedure set against the
set.

## The one command

From this directory, with the Claude Code CLI installed (you have it
if you have been building skills):

    python3 run_eval.py --rubric path/to/your-rubric.md \
        --evidence path/to/your-evidence-guide.md

The grading procedure defaults to the `procedure.md` sitting next to
your rubric, which is the layout of an installed skill copy; pass
`--procedure` to point somewhere else. Point `--rubric` at your
filled rubric and `--evidence` at your filled evidence guide. The
shipped templates (`../skill/rubric.md`,
`../skill/references/evidence-guide.md`, `../skill/procedure.md`) are
empty on purpose, and the skill refuses to grade without them, so
write your checks, your verdict rule, your evidence map, and your
procedure first. Your voice guide is never part of an eval run: eval
mode ignores it by design.

Useful flags: `--limit 3` for a quick smoke run, `--only
pkg-07,pkg-12` to re-grade just the named packages, `--workers N` to
change parallelism (default 5), `--include-calibration` to also grade
the four worksheet packages (they are never scored), `--out
results.json` to keep the full per-check results.

`--only` is the flag for the revise loop: when a full run disagrees on
two packages, re-run only those two while you adjust your components
(about $0.20 per package instead of about $4 for a full run), then
confirm with one full run at the end. Partial runs never print a bar
verdict; only a full 20-package run can pass.

Partial runs also cannot show the category floor, and a revision that
loosens a check can flip a package that agreed before. So when a
revision loosens a check, add canaries to the `--only` list: one
already-agreeing package from each small category the change could
touch (the 2-package `thread-convention` category is the live case),
so a flip shows up at $0.20 instead of on your confirming full run.
The output table's `category` column names each package's category,
so pick canaries straight from your last full run's table: any row in
the right category whose `agree` column says `yes`.
`--include-calibration` composes with `--only`, so a calibration
package your class already resolved works as a free trap check too
(calibration packages carry no score; their agreement shows per item
in the table).

Every run grades with Sonnet, the course's standard model; there is no
model flag. This keeps every student's run (and the instructor
stability runs that set the bar) on the same grader, and Sonnet is the
model your course credit is budgeted for.

## What the output means

One line per package while grading, then a table:

    item    category      gold    verdict  agree  note
    pkg-02  clear-accept  accept  accept   yes
    pkg-04  scope-creep   reject  accept   NO     graded accept
    ...
    categories: clear-accept 7/7  scope-creep 4/4  thread-convention 1/2  unbuildable 3/3  wrong-cause 4/4
    agreement: 19/20 scored items  (bar: 18/20: PASS)

- `category` is the package's composition category, matching the
  `categories:` tally line and the Grading tab's composition table
  (calibration packages show `calib`). This column is where canary
  packages come from.
- `gold` is the instructor label from `gold-labels.json`.
- `verdict` is what the skill decided with YOUR rubric, evidence
  guide, and procedure.
- The `note` column names the checks your rubric failed the package
  on, which is where to look when you disagree with a gold label.
- The `categories` line tallies matches per eval-set composition
  category. Passing needs at least one match in every category (the
  category floor): a rubric that cannot see a whole category, however
  well it does elsewhere, is missing a check the set was built to
  force. The 2-package `thread-convention` category is the live case
  this week: with only two packages, a rubric with no comms checks
  cannot buy the misses back on volume. Partial runs print the
  tallies for
  just the packages graded, plus a reminder that only a full run
  decides the bar and the floor (a calibration-only partial run has
  nothing scored to tally, and says so instead).
- The agreement line is the score the grading bar reads. The bar:
  agreement of 18 of 20 or better passes (exactly 18 passes), AND the
  category floor holds. The 4 calibration packages are never scored.
  Full bar details, including the human read of your components: the
  course portal's Check-In page (`ai301/projects/project_3.md` in this
  repo).

Disagreements are the feedback loop: open the package the table
names, reread the plan against the repro evidence, and decide whether
your check's pass condition, your evidence map, or your procedure is
what needs to move. Then re-run; retries are unlimited.

## What is in a package

Each `packages/*.md` file is self-contained: a real issue's context
(title, body excerpt, thread highlights, and a repo-facts block with
the repo's stated bug-report template asks and contribution policy,
including any AI-use policy), a repro-evidence block (the reproduction
the candidate plan builds on, presented as an accepted week-2-style
report excerpt), a candidate plan, and a candidate plan comment, all
frozen on the capture date stamped at the top. The issue contexts are
real; every repro report, plan, and comment is instructor-authored, so
no real stranger's writing is ever graded here. The harness never
touches GitHub; the skill grades the bundle text, so every run sees
the same world and your score cannot drift because a thread moved on.

Every bundle also has a `.json` twin with the same frozen content in
structured form (issue, thread highlights, repo facts, repro
evidence, plan, plan comment as fields). Read whichever you prefer;
they are the same snapshot. `packages_to_json.py` regenerates the
JSON from the markdown.

## Do not grade the live issue

The `source:` line in each package names the real issue
(`owner/repo#number`). It is deliberately not a link: the real issue
has kept moving since the capture date, with new comments, new linked
PRs, sometimes a fix already merged. That is exactly why the
snapshots exist. The gold labels describe the snapshot, not today's
GitHub. When the live page and the bundle disagree, the bundle wins.

## Format note

This markdown-plus-manifest layout is the browsable form of the
eval-set format used in production model evals: one record per item
with input, gold label, and metadata (usually JSONL), a judge prompt
(here, the skill plus your rubric, evidence guide, and procedure),
and a scoring script (here, `run_eval.py`). Third week on the same
instrument: the judged artifact keeps getting less mechanical, and
the instrument does not change.
