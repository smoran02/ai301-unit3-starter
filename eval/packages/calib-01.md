# Eval package: calib-01

- source: jesseduffield/lazygit#5900
- captured: 2026-08-18
- calibration: true

## Repo facts (captured 2026-08-18)

- repo: jesseduffield/lazygit (81423 stars, archived: no)
- description: Simple terminal UI for git commands.
- latest release: v0.64.1 (2026-08-12)
- bug reports: template asks for the lazygit version, git version, operating system, and a description with steps
- contribution policy (CONTRIBUTING.md): the maintainer reviews outside pull requests only selectively (maintaining is a hobby and review time is scarce, especially with AI-generated PRs hard to assess); issue reports remain welcome; no stated AI disclosure requirement

## Issue

### In commits of local branch a push does not refresh the color of the commit (#5900)

opened by chhil (NONE) on 2026-08-06, state open, labels: bug

In the Local Branches window, double click into a branch's commits.
An unpushed commit shows in the unpushed color. Push it: the color
does not change, though the commit was pushed. Escaping out to
branches and coming back into commits refreshes the color to indicate
it is no longer local.

Expected: a color change to reflect a successful push.

Version: 0.64.0 (Homebrew), macOS, git 2.55.0.

## Thread highlights (0 comments total)

(no comments)

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: lazygit 0.64.1 (Homebrew), git 2.55.0, macOS 14.5,
iTerm2; test repo with an origin remote.

Steps:

1. Made a local commit, opened Local Branches, entered the branch's
   commits view: the new commit renders in the unpushed color
   (yellow) and the older pushed ones in the default color.
2. Pressed `P` to push from that view. Push succeeded (remote ref
   updated; confirmed with `git log origin/main -1` in another
   shell).
3. The commit still renders in the unpushed color in the open
   commits view.
4. Pressed Esc to branches, re-entered commits: the commit now
   renders in the pushed color.

Expected: step 3 shows the pushed color without leaving the view.

Actual: the color updates only after exiting and re-entering,
matching the issue.

## Candidate plan

Cause: after a push started from the branch-commits view, that view's
model is not refreshed, so the commits keep their pre-push
push-status flags until the view is rebuilt on re-entry.

Change: trigger a refresh of the commits context after a successful
push. In: the push completion callback in
`pkg/gui/controllers/sync_controller.go` adds the commits context to
its post-push refresh scope. Out: any change to how push status is
computed, or to other views' refresh behavior.

Test: repro steps above; at step 3 the color must flip without
leaving the view. Also check the same from the main commits panel and
after a force push, since both share the callback.

## Candidate plan comment

Reproduced on 0.64.1 (report above). The post-push refresh scope
just misses the branch-commits context; plan is a one-change fix in
the sync controller's push callback plus a manual check across the
two commit views and force push. Will send the PR shortly; keeping
it minimal given the review-bandwidth note in CONTRIBUTING.
