# Eval package: pkg-17

- source: jesseduffield/lazygit#5703
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: jesseduffield/lazygit (81423 stars, archived: no)
- description: Simple terminal UI for git commands.
- latest release: v0.64.1 (2026-08-12)
- bug reports: template asks for the lazygit version, git version, operating system, and a description with steps
- contribution policy (CONTRIBUTING.md): the maintainer reviews outside pull requests only selectively (maintaining is a hobby and review time is scarce, especially with AI-generated PRs hard to assess); issue reports remain welcome; no stated AI disclosure requirement

## Issue

### Main panel scrolling broken when running lazygit under tmux with 0.62.x versions (#5703)

opened by scodougy (NONE) on 2026-06-16, state open, labels: bug

Selecting a file to view diffs, the main pane shows the text but is
no longer scrollable when running under tmux. Raw gnome-terminal
works fine; in a tmux session the scroll wheel scrolls the wrong
pane, and the diff panel cannot be selected with the mouse. It worked
fine in 0.61.x. Probably related: the repo selector (ctrl-R) also
cannot be driven by mouse.

Versions: 0.62.1, 0.62.2. Terminal: tmux within gnome-terminal on
Mint/Cinnamon and LMDE.

## Thread highlights (12 comments total)

- 2026-06-21 rasadov (NONE): offers to dig in, describes a freeze; the reporter clarifies their symptom is wrong-pane scrolling, not a freeze
- 2026-06-22 stefanhaller (COLLABORATOR): cannot reproduce under tmux 3.6b with no config; scrolling works; wonders about configuration interplay
- 2026-06-28 stefanhaller (COLLABORATOR): tried a Ubuntu VM with gnome-terminal and tmux 3.7 as well; works fine; "I'm honestly not sure what to do with this issue"
- 2026-06-28 scodougy (NONE): isolated it to `set -g mouse on` in their tmux.conf; with that line removed, 0.62.x behaves

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: lazygit 0.62.2 (binary release), git 2.55.0, tmux 3.2a
with `set -g mouse on` in tmux.conf, gnome-terminal, Linux Mint 21.3.

Steps:

1. Started tmux (mouse on), opened lazygit in a git repo, selected a
   file so the main panel shows a long diff.
2. Scroll wheel over the main panel: the files panel scrolls instead;
   the main panel selection cannot be moved by mouse.
3. Control: same tmux with `set -g mouse off`: wheel scrolls the main
   panel correctly.
4. Control: lazygit 0.61.1, same tmux with mouse on: wheel scrolls
   the main panel correctly.

Expected: 0.62.x scrolls the hovered panel under tmux mouse mode, as
0.61.x does.

Actual: with tmux `mouse on`, 0.62.x routes wheel events to the wrong
panel; toggling either the tmux option or the lazygit version flips
the behavior, so the regression is in how 0.62.x consumes tmux's
mouse reporting.

## Candidate plan

The mouse handling clearly changed somewhere between 0.61 and 0.62,
so the plan is to figure out what happened and make scrolling work
under tmux again.

Steps:

1. Investigate how lazygit reads mouse events (gocui? tcell? not
   sure which layer is responsible) and how tmux's mouse mode changes
   what arrives.
2. Try different mouse protocols and see if one of them behaves
   better under tmux.
3. Look at what changed in 0.62 that could affect this.
4. Fix the scrolling once the cause is clear.

Test plan: scrolling should work correctly under tmux afterwards,
and nothing else should feel broken.

## Candidate plan comment

I can reproduce this exactly (report above, including the mouse-on
isolation). I want to take a crack at fixing it: I'll investigate the
input stack and the tmux interaction, experiment with the mouse
protocols, and track down whatever changed in 0.62. Will post a fix
once scrolling behaves.
