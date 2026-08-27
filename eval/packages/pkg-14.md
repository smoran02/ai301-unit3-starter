# Eval package: pkg-14

- source: zellij-org/zellij#5174
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: zellij-org/zellij (34973 stars, archived: no)
- description: A terminal workspace with batteries included.
- latest release: v0.44.3 (2026-05-13)
- bug reports: template asks for an issue description, a minimal reproduction, and other relevant information (zellij version, terminal, OS)
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Zellij 0.44.2: OSC color sequences leak into terminal on session reattach via SSH (#5174)

opened by carlosemart (NONE) on 2026-05-14, state open, labels: suspected bug

When attaching to an existing session over SSH, Zellij 0.44.2 prints
raw OSC terminal color response sequences directly into the terminal
output instead of consuming them internally, producing visible
garbage such as `rgb:8787/d7d7/5f5f` strings (apparently OSC 4 / OSC
10 / OSC 11 color query responses).

Important behavior difference from the report: the issue does NOT
occur when the session is first created; it appears after detaching
and re-attaching, which suggests the problem is specific to reattach
state restoration. It occurs in 0.44.2 but not 0.44.1 with the same
setup.

Minimal reproduction:

1. `ssh testhost -t zellij attach -c implacable-tambourine`
2. The session behaves correctly.
3. Detach, then re-run the same command to re-attach.
4. Raw OSC color responses are printed into the terminal.

Environment: zellij 0.44.2, WezTerm, connection over SSH.

## Thread highlights (6 comments total)

- 2026-05-19 vtomCD (NONE): similar behavior when switching between sessions on Windows in WezTerm (0.44.3)
- 2026-05-27 epoweripione (NONE): same on Debian 13 with zsh, 0.44.3
- 2026-06-23 aidnem (NONE): same on Windows PowerShell when attaching, no SSH involved
- 2026-07-30 jeromejanicot (NONE): clearing `~/.cache/zellij` gives one clean launch; the leak returns once the cache folder is recreated; no issues on macOS with WezTerm or Ghostty

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: zellij 0.44.3 (cargo install) on Ubuntu 24.04 (server),
attached from WezTerm 20240203 on macOS 14.5 over SSH; zsh 5.9.

Steps:

1. `ssh testhost -t zellij attach -c repro-session`: clean first
   attach, normal session.
2. Detached with `Ctrl-o d`.
3. Re-ran the same ssh command to re-attach.
4. On re-attach, several lines of raw color strings printed into the
   pane, of the form `rgb:1c1c/1c1c/1c1c` and fragments interleaved
   with prompt output (copied verbatim into the report).
5. Repeated detach/attach 5 times: the leak appeared on every
   re-attach, never on a fresh session create.

Control runs:

- Same host and terminal on zellij 0.44.1: 5 reattach cycles, no
  leak.
- After `rm -rf ~/.cache/zellij` (thread observation): the next
  attach is clean, the one after leaks again.

Expected: reattach consumes color query responses internally, as
first attach does.

Actual: every reattach on 0.44.x from 0.44.2 on prints the raw OSC
responses, matching the issue; the regression window and cache
observation both reproduce.

## Candidate plan

Diagnosis: on reattach, zellij issues OSC 4/10/11 color queries to
the client terminal (used for theme detection) but the reattach path
wires the client's stdin to the session before the query responses
have been consumed, so the responses arrive as ordinary input and are
echoed into the active pane. Grounded in the repro: fresh attach
(which performs the same queries behind the loading screen) is clean,
the leak starts exactly at reattach, and 0.44.1, which predates the
reattach-path change in 0.44.2, is clean on the same setup. The cache
control fits: with an empty cache the color data is refetched along
the fresh-attach path once.

Scope, one bounded change: the reattach handshake on Unix clients.
In scope: consuming or draining pending OSC query responses in the
client attach path in `zellij-server`'s client connection handling
before pane input is wired. Explicitly deferred, with reasons: the
Windows session-switch variant reported in the thread (I cannot test
Windows; the fix site may be shared, and I will say so in the PR so
someone with a Windows setup can verify) and any change to how theme
detection caches its results.

Files: the client attach/reattach path in `zellij-server` (session
connection handling) and `zellij-client`'s terminal query issuance;
exact functions to be pinned in the PR after tracing the query
issuance with debug logs, which I have working (the leak's origin is
visible in `zellij --debug` output).

Test plan: the repro loop: 5 consecutive SSH reattach cycles with no
rgb strings in any pane; fresh-create still clean; 0.44.1 behavioral
parity restored on the regression command sequence. The cache
control (one clean attach after cache clear) must become "always
clean".

Risk: draining input at attach risks eating one legitimate keystroke
typed during the handshake window; I will bound the drain to OSC
response patterns rather than a time window, and call that decision
out for review.

## Candidate plan comment

I reproduced this over SSH with a clean regression window (0.44.1
clean, 0.44.2 on leaking; report above, including the cache
observation from this thread). Plan: consume pending OSC color query
responses in the reattach handshake before pane input is wired,
bounded to the Unix client path. I cannot test the Windows
session-switch variant reported here, so I am explicitly leaving it
out and will flag the shared fix site in the PR for someone with a
Windows setup to verify. Report-back once I have the handshake
change behind the repro loop.
