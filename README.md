# AI301 Unit 3 starter: plan-check

Materials for Unit 3 of AI301 (plan and build). This repo holds the
week's runnable artifacts: the plan-check skill and its eval harness.
All instructions live on the course portal (Overview, Activity, and
Check-In tabs for Unit 3); this repo is the package those pages tell
you to install and run.

## What's here

- `skill/`: the plan-check skill for Claude Code, complete except for
  three authored components: `skill/rubric.md`,
  `skill/references/evidence-guide.md`, and `skill/procedure.md` ship
  as templates (your voice guide pastes forward from Unit 2 into its
  carry-over slot). Filling them is the Unit 3 deliverable.
- `eval/`: the eval harness, the gold labels, and 24 frozen packages
  (20 scored plus the 4 calibration packages from the in-class
  activity). See `eval/README.md` for the full run and output guide.

## Install the skill

Copy the whole `skill/` folder to `~/.claude/skills/plan-check/`
(create the folders if they do not exist). Edit your components inside
that installed copy and point the harness at the same files, so eval
runs and live runs share one canonical set (the procedure is picked up
automatically from next to the rubric).

## Run the eval

From `eval/`, with the Claude Code CLI installed:

    python3 run_eval.py --rubric path/to/your-rubric.md \
        --evidence path/to/your-evidence-guide.md

`--limit 3` gives a smoke run. Full docs: `eval/README.md`.
