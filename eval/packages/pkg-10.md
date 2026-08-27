# Eval package: pkg-10

- source: starship/starship#7677
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: starship/starship (59457 stars, archived: no)
- description: The minimal, blazing-fast, and infinitely customizable prompt for any shell!
- latest release: v1.26.0 (2026-06-28)
- bug reports: template asks reporters to file via `starship bug-report` (pre-populates the system configuration) and to give current behavior, expected behavior, environment (starship version, shell type and version, OS), and the relevant starship configuration
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Git related modules are extremely slow on windows (#7677)

opened by FlyinCow (NONE) on 2026-08-17, state open, labels: bug

The docs note the git status module is very slow in Windows
directories under WSL and suggest the `windows_starship` option, but
the reporter is using Windows git with Windows starship and it is
still slow when entering a git folder. Both starship and git are
installed via scoop; the reporter suspects scoop-installed git may be
involved, since the GitHub CLI also misbehaves with it.

Environment from the report: starship 1.26.0, PowerShell 5.1, Windows
10.0.26200, vscode terminal, rust 1.96.0 build.

Expected behavior, as stated in the report: "Faster."

## Thread highlights (0 comments total)

(no comments)

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: starship 1.26.0 (scoop), git 2.51.0.windows.1 (scoop),
PowerShell 5.1, Windows 10 build 26200; test repo: a clone of
kubernetes/kubernetes (large working tree, clean state).

Steps:

1. `cd` into the test repo with the default starship config
   (git_branch and git_status enabled).
2. Measured prompt latency with starship's own timer:
   `starship timings` after rendering the prompt.

Artifact (abridged `starship timings` output):

```
 git_status  -  1873ms
 git_branch  -    41ms
 directory   -     2ms
```

3. Control: same directory with `git_status.disabled = true` in
   starship.toml: total prompt time drops under 100ms.
4. Control: same steps in a 10-file repo: git_status 38ms.

Expected: prompt latency in the same ballpark as `git status`
itself, which takes about 350ms in this repo from the same shell.

Actual: git_status dominates the prompt at about 1.9s on the large
repo, about 5x the cost of running `git status` directly, matching
the reported slowness.

## Candidate plan

The git modules on Windows clearly have performance problems, so the
plan is to dig into where the time goes and speed them up.

Steps:

1. Profile starship on Windows to find the slow parts of the git
   modules.
2. Investigate whether scoop-installed git behaves differently from
   the official installer, since the reporter and I both use scoop.
3. Look into caching git information between prompts so repeated
   renders are cheaper.
4. Optimize whatever the profiling turns up, and consider spawning
   fewer git subprocesses in general.

Test plan: after optimizing, the prompt should feel fast in big repos
on Windows, and `starship timings` should look much better.

## Candidate plan comment

This matches what I see on my machine too, so I profiled it a bit
(numbers above) and git_status is where the time goes. I am going to
investigate the git modules' performance on Windows, look at the
scoop angle, and explore caching between prompts. Will optimize
whatever shows up hot and report back when things are faster.
