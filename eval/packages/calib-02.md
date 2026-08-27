# Eval package: calib-02

- source: laurent22/joplin#15309
- captured: 2026-08-18
- calibration: true

## Repo facts (captured 2026-08-18)

- repo: laurent22/joplin (55986 stars, archived: no)
- description: Joplin, the privacy-focused note taking app with sync capabilities for Windows, macOS, Linux, Android and iOS.
- latest release: v3.6.15 (2026-06-20)
- bug reports: template asks for the operating system, the Joplin version, desktop version info, current behavior, expected behavior, and logs
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Can't undo after toggle editor change (markdown vs wytiwys) (#15309)

opened by zhizhongpu (NONE) on 2026-05-09, state open, labels: bug, stale

Joplin 3.6.11 (prod, darwin), macOS, Rich Text editor.

Current behavior:

1. Write something in the markdown editor.
2. Toggle editor to wysiwyg (via the Toggle editors shortcut).
3. Toggle back to markdown.
4. Undo.
5. Step 1's text is not reverted.

Expected: after the round-trip toggle, undo reverts the step-1 edit.

## Thread highlights (7 comments total)

- 2026-06-15 zhizhongpu (NONE): still present in 3.6.13 and 3.6.14; asks for the stale label to be removed
- 2026-07-17 zhizhongpu (NONE): not fixed (replying to the stale bot again)

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: Joplin 3.6.15 (prod, darwin), macOS 14.5, Apple M2;
fresh profile, Markdown editor default.

Steps:

1. New note, typed `undo target line` in the markdown editor.
2. Toggled to the rich text editor and back (Toggle editors
   shortcut, twice).
3. Pressed Cmd+Z in the markdown editor.

Artifact: screen recording described in the report; the note still
contains `undo target line` after step 3, and further Cmd+Z presses
do nothing. Control: without the toggle round-trip, Cmd+Z after step
1 removes the typed line as expected.

Expected: undo reverts the step-1 edit after the toggle round-trip.

Actual: the editor's undo stack no longer contains the edit after
toggling, matching the issue on current 3.6.15.

## Candidate plan

Honestly this one seems really annoying and I'd love to fix it! Undo
is probably handled somewhere in the editor code, maybe per-editor,
so the undo stack must be getting lost when the editors switch. My
plan is to poke around the editor components this weekend, figure out
where the undo history lives, and send a PR that makes undo work
across toggles. Should be doable in a few evenings.

Test plan: undo works after toggling.

## Candidate plan comment

This bug has been bugging me too, so I'm going to fix it! I'll dig
into the editor code this weekend and should have a PR up soon that
makes undo survive the editor toggle. Wish me luck!
