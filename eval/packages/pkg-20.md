# Eval package: pkg-20

- source: ghostty-org/ghostty#11261
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: ghostty-org/ghostty (59808 stars, archived: no)
- description: Ghostty is a fast, feature-rich, and cross-platform terminal emulator that uses platform-native UI and GPU acceleration.
- latest release: v1.3.1
- bug reports: template asks for the ghostty version, configuration, and platform details; first-time contributors go through a vouch flow before PRs are accepted
- contribution policy (CONTRIBUTING.md + AI_POLICY.md): strict AI rules. All AI usage in any form must be disclosed, stating the tool used and the extent of the assistance; the human in the loop must fully understand the work; AI-assisted issues and comments must be reviewed and edited by a human before submission

## Issue

### crash: capacity changes during print with managed memory can be unsafe (#11261)

opened by mitchellh (CONTRIBUTOR) on 2026-03-09, state open, labels: crash, vt

From #11249. A fuzz-found crash where `Terminal.print` keeps a stale
pointer to the previous cell when a hyperlink write causes page
growth. Reduced test case (abridged):

```zig
test "Terminal: grapheme append after hyperlink growth" {
    var t = try init(alloc, .{ .cols = 80, .rows = 24 });
    defer t.deinit(alloc);
    t.modes.set(.grapheme_cluster, true);
    try t.screens.active.startHyperlink("h", null);
    try t.printString("HeHelloooooooo");
    for (0..4) |_| try t.print(0x1E);
    for (0..45) |_| try t.print(0xFFFD);
    try t.print(0x0600);
    try t.print(0xFFFD);
}
```

Stack (abridged): panic, reached unreachable code, assert at
`src/terminal/page.zig:1487` in `appendGrapheme`
(`assert(cell.codepoint() != 0)`), reached from
`Screen.appendGrapheme` and `Terminal.print`.

## Thread highlights (2 comments total)

- 2026-03-09 mitchellh (CONTRIBUTOR): the AI-proposed solution was to recompute `prev` at every point it is used, but that is too expensive for this hot path; proposes instead recomputing `prev` only if the underlying page capacity changed during an operation, and notes there are multiple ways to detect that worth comparing for cost
- 2026-03-09 mitchellh (CONTRIBUTOR): adds a second fuzz-derived test case where print's grapheme `.wide` branch holds `prev.cell` across a spacer-tail print that grows hyperlink storage

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: ghostty built from source at main (2026-08 checkout),
zig 0.15.2, macOS 14.5 (arm64); slow_runtime_safety build options on.

Steps:

1. Added the issue's reduced test case verbatim to
   `src/terminal/Terminal.zig`'s test block and ran
   `zig build test` filtered to it.

Artifact:

```
thread panic: reached unreachable code
.../std/debug.zig:559:14: in assert
src/terminal/page.zig:1487:54: in appendGrapheme
        if (build_options.slow_runtime_safety) assert(cell.codepoint() != 0);
src/terminal/Screen.zig:2139:50: in appendGrapheme
src/terminal/Terminal.zig:533:51: in print
```

2. The issue's second test case (VS16 widening with full hyperlink
   map) panics on the same assert.

Control: the same first test with the hyperlink start removed (no
page growth mid-print) passes, isolating the growth-during-print as
the trigger.

Expected: both tests pass; grapheme append lands on the real
previous cell after any mid-print page growth.

Actual: the stale `prev` pointer survives the capacity change and
the append hits a zeroed cell, tripping the assert, matching the
issue on current main.

## Candidate plan

Diagnosis: as the issue states and the repro isolates: `prev` (the
cached previous-cell pointer in `Terminal.print`) goes stale when a
mid-print operation (hyperlink storage growth) reallocates the page,
and the grapheme append then dereferences into the reallocated
memory.

Scope, one bounded change, following the direction already given in
the thread: detect capacity change and recompute `prev` only then.
In scope: `Terminal.print`'s grapheme paths (including the `.wide`
branch from the second test) and a cheap change-detection mechanism
on the page. Not in scope: recomputing `prev` unconditionally (the
approach the thread already rejected as too expensive), or any wider
refactor of page memory management.

Approach:

1. Add a monotonic generation counter to the page that increments on
   any capacity-changing operation (the thread notes multiple
   detection options; the counter is the cheapest I can see: one
   integer bump on realloc, one comparison per use).
2. In `Terminal.print`, snapshot the generation next to `prev`;
   before any use of `prev.cell`, compare and recompute the pointer
   from the pin when the generation moved.
3. Add both of the issue's test cases as regression tests, plus the
   no-hyperlink control.

Test plan: `zig build test` with both fuzz-derived cases passing and
the control unchanged; re-run the fuzzer corpus from #11249 against
the build overnight and report the result in the PR.

Risk, stated: I have not yet measured the per-print cost of the
generation comparison; if it shows up in the print benchmark I will
move the check to the two growth-adjacent call sites only, and I
flag that trade-off for review. Whether other cached pointers in
print (beyond `prev`) can go stale the same way is an open question
I would leave to a follow-up unless review says otherwise.

## Candidate plan comment

I reproduced both fuzz cases on current main (report above; the
no-hyperlink control isolates growth-during-print as the trigger).
My plan follows the direction proposed here: a page generation
counter bumped on capacity changes, with `prev` recomputed in
`Terminal.print` only when the generation moved, so the hot path
stays one comparison. Both test cases land as regression tests and
I'll run the #11249 corpus against the build before the PR. One open
question flagged in the plan: whether the check should live per-use
or only at the two growth-adjacent sites, pending the print
benchmark.
