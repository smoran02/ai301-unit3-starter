# Eval package: pkg-02

- source: sharkdp/bat#3844
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: sharkdp/bat (60197 stars, archived: no)
- description: A cat(1) clone with wings.
- latest release: v0.26.1 (2025-12-02)
- bug reports: template asks what steps reproduce the bug, what happens, what you expected, how you installed bat, and for the output of `bat --version` plus environment details
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### bat panics (capacity overflow) on `--terminal-width 1` wrapping a double-width char with a background (#3844)

opened by leeewee (NONE) on 2026-07-17, state open, labels: bug

`bat --terminal-width 1 --wrap character` aborts with `capacity
overflow` (exit 101) when a line contains a character wider than the
terminal (a double-width CJK char or emoji) and a background is
painted on that line (`--highlight-line`, or a theme/style that fills
the row background). The same defect class as the `--style=snip`
width-1 panic (#3803).

```
$ printf '📦📦\n' | bat --highlight-line 1 --terminal-width 1 --wrap character \
                       --color always --paging never --theme OneHalfDark
thread 'main' panicked at library/alloc/src/slice.rs:524:23:
capacity overflow
$ echo $?
101
```

Root cause per the report: in `InteractivePrinter::print_line`
(`src/printer.rs`), wrapping branch, `cursor_max` is the terminal
width (line 692) and `cursor` accumulates each chunk's display width.
When a chunk is wider than the remaining width, `cursor` overshoots
`cursor_max`, and the end-of-line background fill at line 934 computes
`" ".repeat(cursor_max - cursor)`, a usize subtraction that underflows
and aborts inside `str::repeat`. The sibling cursor advance at line
795 is the same tiny-width/wide-char pairing.

Expected: a terminal narrower than a single glyph should clamp the
background fill to empty, not underflow and abort, mirroring the
clamping bat already applies elsewhere.

## Thread highlights (0 comments total)

(no comments)

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: bat 0.26.1 (cargo install, rustc 1.96.0), Arch Linux,
xterm-256color.

Steps:

```
$ printf '📦📦\n' | bat --highlight-line 1 --terminal-width 1 --wrap character \
                       --color always --paging never --theme OneHalfDark
thread 'main' panicked at library/alloc/src/slice.rs:524:23:
capacity overflow
$ echo $?
101
```

Control run, width 2 (equal to the glyph's display width):

```
$ printf '📦📦\n' | bat --highlight-line 1 --terminal-width 2 --wrap character \
                       --color always --paging never --theme OneHalfDark
📦
📦
$ echo $?
0
```

Second control: same width-1 command without `--highlight-line` (no
background painted) exits 0.

Expected: clamped output (or empty fill) at width 1, exit 0.

Actual: abort with `capacity overflow`, exit 101, exactly when the
line carries a background and a glyph wider than the terminal.

## Candidate plan

Diagnosis: the width-1 abort is the usize underflow the issue pins at
`src/printer.rs:934`: `cursor` overshoots `cursor_max` when a chunk's
display width exceeds the remaining width, and the background fill
subtracts past zero. Both controls in the repro fit: no background, no
subtraction; width 2, no overshoot.

Change, one fix: clamp the fill with `saturating_sub` (fill length 0
when `cursor` overshot), and apply the same clamp to the sibling
cursor advance at line 795 so the cursor never overshoots in the
first place. Audit the two other `cursor_max - cursor` sites in
`print_line` for the same pattern. Not in scope: redesigning wide-char
wrapping at tiny widths (the visual result at width 1 stays imperfect;
this fix removes the abort).

Files: `src/printer.rs` (the two subtraction sites), `tests/` (one
regression case).

Test plan: re-run the repro command, expect drawn output and exit 0;
re-run both controls unchanged; add the repro as an integration test
pinned at width 1. Risk: other underflow-prone width arithmetic may
exist outside `print_line`; I will grep printer.rs for bare `-` on
cursor variables and note anything suspicious in the PR rather than
fixing beyond this issue.

## Candidate plan comment

I can take this one. Repro'd on 0.26.1 (report above): the underflow
is the background-fill subtraction the issue points at, plus its
sibling advance. Plan: saturating clamps at both sites in
`src/printer.rs`, a width-1 regression test, nothing beyond the abort
(same class as #3803, so I'll mention it in the PR for the
maintainers' cross-reference). Report-back once the test is in.
