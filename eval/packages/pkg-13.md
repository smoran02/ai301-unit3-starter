# Eval package: pkg-13

- source: microsoft/terminal#20370
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: microsoft/terminal (104620 stars, archived: no)
- description: The new Windows Terminal and the original Windows console host, all in the same place!
- latest release: v1.24.11911.0 (2026-07-16)
- bug reports: template asks for the Windows Terminal version, the Windows build number, other relevant software, steps to reproduce, expected behavior, and actual behavior
- contribution policy (CONTRIBUTING.md): standard contribution guide with a CLA; no stated AI policy

## Issue

### WT scrolls to top if in scrollback & scrollback cleared `ESC[3J` (#20370)

opened by petrroll (NONE) on 2026-06-28, state open, labels: Product-Conhost, Area-Rendering, Area-VT, Issue-Bug, Product-Terminal, Impact-Visual, Area-AtlasEngine

Windows Terminal 1.24.11321.0, Windows build 10.0.26310.0.

Steps:

1. Have some scrollback.
2. Scroll a bit up into the scrollback area.
3. Have the running app emit `ESC[3J` (erase scrollback).

The issue includes a small node script that emits `ESC[3J`
periodically; scroll up while it runs and the viewport jumps to the
absolute top after a moment. Other terminals such as alacritty do not
do this.

Expected: the view jumps to the bottom (or possibly stays where it
was), as in alacritty and many other terminals.

Actual: the view jumps to the absolute top.

## Thread highlights (5 comments total)

- 2026-06-28 lebensterben (NONE): also occurs in the Preview build; mouse selection also misbehaves, as if the terminal keeps snapping to the prompt position
- 2026-07-08 DHowett (MEMBER): "That ain't right."
- 2026-07-08 DHowett (MEMBER): reproduced it, and the content disappeared after a while: "Oh, it's a RENDERING bug!"
- 2026-07-08 DHowett (MEMBER): "We haven't had a classic invalidation bug in quite some time. Good find!"

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: Windows Terminal 1.24.11911.0 (Store), Windows 11 build
26100; node 22 for the repro script.

Steps:

1. Ran a script printing 500 numbered lines, then emitting `ESC[3J`
   every 2 seconds while printing one line per second (equivalent to
   the issue's attached script).
2. Scrolled up about 30 lines into scrollback.
3. Within one interval, the viewport jumped to the very top row of
   the buffer (row 1 visible, scrollbar thumb at the top).
4. Waited: after two more intervals, previously visible lines
   rendered blank until a window resize forced a repaint (the
   disappearing-content behavior a maintainer also reproduced).

Control: the same script in alacritty 0.15: on `ESC[3J` the view
snaps to the bottom prompt line; no blanking.

Expected: bottom snap (or stay in place), and no stale blank regions.

Actual: top jump plus stale rendering until a forced repaint,
matching the issue and the maintainer's rendering-bug observation.

## Candidate plan

Diagnosis: grounded in the repro and the maintainer's confirmation
that this is an invalidation bug: when `ESC[3J` deletes the
scrollback while the user's viewport is scrolled into it, the
viewport offset is left pointing at removed rows (clamping lands it
at the top) and the renderer is not invalidated for the shifted
region (the blanking in step 4).

Scope, one bounded change: the erase-scrollback path. In scope: the
`ESC[3J` (erase scrollback) handler in the VT adapter
(`AdaptDispatch::EraseInDisplay`, scrollback branch) and the
invalidation it hands the renderer. Not in scope: the mouse-selection
misbehavior noted in the thread (worth its own issue; I will file it
separately with a repro), and any general scrollback redesign.

Approach:

1. In the erase-scrollback branch, re-anchor the user's viewport
   relative to the mutable viewport (bottom) instead of letting the
   clamp land at buffer top, mirroring the bottom-snap behavior the
   control terminal shows.
2. Invalidate the full visible region after the buffer rotation so
   the Atlas engine repaints shifted rows (the stale-blank symptom).
3. Add a unit test in the adapter tests covering viewport position
   after `ESC[3J` with an offset viewport.

Test plan: re-run the repro script; scrolled-up viewport must snap to
the bottom on the next `ESC[3J` (not top), and no region may render
blank afterward (no resize needed). The alacritty control is the
behavioral reference. Adapter unit test as above.

Risk: conhost and Terminal share this path; I will run the same
repro in conhost to check for a divergent regression, and I have not
yet verified which layer clamps the viewport, so the exact fix site
within the branch may move one level during implementation (named as
an unknown, not a certainty).

## Candidate plan comment

I reproduced both halves of this on 1.24.11911.0, the top jump and
the stale blank region that DHowett called out as an invalidation bug
(report above, with alacritty as the reference behavior). Plan: fix
the viewport re-anchor and renderer invalidation in the
erase-scrollback branch of `EraseInDisplay`, with an adapter unit
test; the mouse-selection symptom from the thread I would file
separately rather than fold in. Flagging that the exact clamp site
may be one layer up or down from where I have it; I will confirm
while implementing and say so in the PR.
