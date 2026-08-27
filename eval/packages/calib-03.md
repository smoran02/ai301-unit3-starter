# Eval package: calib-03

- source: sharkdp/bat#3831
- captured: 2026-08-18
- calibration: true

## Repo facts (captured 2026-08-18)

- repo: sharkdp/bat (60197 stars, archived: no)
- description: A cat(1) clone with wings.
- latest release: v0.26.1 (2025-12-02)
- bug reports: template asks what steps reproduce the bug, what happens, what you expected, how you installed bat, and for the output of `bat --version` plus environment details
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Seeking to the end of a file is unreasonably slow (#3831)

opened by kodnisse (NONE) on 2026-07-06, state open, labels: bug

Steps: open a large file (about 100k lines), seek to the end with
`shift + G`. Seeking to the end of `/var/log/pacman.log` (94000
lines) using bat takes over 25 seconds on the reporter's machine.
Seeking to the end of the same file with `less` is immediate; the
reporter expects the same from bat's pager.

bat 0.26.1, Arch Linux, default config with `--theme='OneHalfDark'`.

## Thread highlights (4 comments total)

- 2026-07-06 keith-hall (COLLABORATOR): a known problem with no current solution; see the long-running thread in #304
- 2026-07-06 kodnisse (NONE): "It appears the syntax highlighting is at fault. Disabling colors made it magnitudes faster."
- 2026-07-10 Amilliox (NONE): claims a root cause: `HashedEventRegister` in output.rs overriding all default `minus` pager bindings, registering only home and end, leaving search and navigation keys unbound; says it is fixed in PR #3836 by adding the default bindings before the custom ones

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: bat 0.26.1 (pacman), Arch Linux, xterm-256color; test
file: `/var/log/pacman.log` equivalent generated at 94,000 lines.

Steps and timings (each repeated 3 times, median reported):

1. `bat big.log`, pressed shift+G in the pager: end of file reached
   after 26.4 s.
2. `bat --color=never big.log`, pressed shift+G in the same pager:
   end of file reached in under 0.3 s.
3. `time bat --color=always --paging=never big.log > /dev/null`
   (no pager in the loop at all): 25.8 s wall time.
4. `time bat --color=never --paging=never big.log > /dev/null`:
   0.2 s.

Expected: shift+G lands at the end of the file in about the time
`less` takes (immediate).

Actual: with highlighting on, reaching the end takes about 26 s
whether or not the pager is involved at all (step 3); with
highlighting off, the same pager seeks instantly (step 2). The wait
tracks the highlighting work, and the pager can only show the last
line once the highlighted lines exist.

## Candidate plan

### Summary

Restore instant end-of-file seeking in bat's pager by repairing the
pager's key-binding registration, which currently drops the default
`minus` navigation bindings.

### Diagnosis

As identified in this thread, `HashedEventRegister` in `src/output.rs`
overrides all of the `minus` pager's default bindings and registers
only `home`/`end`. With the default bindings gone, `shift+G` falls
through to a degraded navigation path that walks the buffer line by
line instead of jumping, which is why reaching the end of a 94k-line
file takes tens of seconds.

### Scope

In scope: the binding registration in `src/output.rs`. Not in scope:
the syntax highlighting pipeline, which is unrelated to pager
navigation.

### Changes

1. Call `minus::input::generate_default_bindings()` before
   registering bat's custom bindings, so the full default navigation
   set (search keys, `G`, `g`, page keys) is present.
2. Override only `home`/`end` afterwards, preserving bat's two
   customizations.
3. Add a pager-integration smoke test asserting the default binding
   set is registered.

### Test plan

Open the 94k-line log, press shift+G: the pager lands on the last
line immediately, matching `less`. Verify `/`, `?`, `n`, `N` search
bindings work in the same session, since the same registration bug
swallows them.

## Candidate plan comment

I traced this to the pager key-binding registration issue identified
above: bat's `HashedEventRegister` wipes the default `minus`
bindings, so end-of-file seeking degrades to a line walk. My plan
restores the defaults before applying bat's two overrides, with a
smoke test on the binding set, and brings back instant shift+G plus
the missing search keys in one contained change to `src/output.rs`.
