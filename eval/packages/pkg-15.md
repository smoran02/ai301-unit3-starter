# Eval package: pkg-15

- source: laurent22/joplin#16215
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: laurent22/joplin (55986 stars, archived: no)
- description: Joplin, the privacy-focused note taking app with sync capabilities for Windows, macOS, Linux, Android and iOS.
- latest release: v3.6.15 (2026-06-20); the issue targets the 3.7.10 prerelease
- bug reports: template asks for the operating system, the Joplin version, desktop version info, current behavior, expected behavior, and logs
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### WebDAV sync ETIMEDOUT returns in 3.7.10: 250 ms autoSelectFamily timeout aborts slow connections (#16215)

opened by PandaWood (NONE) on 2026-08-16, state open, labels: bug

Follow-up to #16201: the previously linked fix addressed a WebDAV
header rejection, which cannot produce an ETIMEDOUT; that symptom has
a separate root cause, now isolated.

Environment: Joplin 3.7.10 (AppImage), Electron 42.3.0, bundled Node
24.15.0, Arch-based Linux; sync target WebDAV (Koofr).

Current behavior: sync fails intermittently with
`FetchError: ... reason: Code: ETIMEDOUT` from node-fetch, while
`curl` and a current system Node succeed instantly against the same
URL. The UI reports "Synchronisation finished" with no visible error
(related: #12810).

Root cause per the report: Node's Happy Eyeballs implementation
(`autoSelectFamily`) races connection attempts and aborts each after
`autoSelectFamilyAttemptTimeout`, which defaults to 250 ms in the
bundled runtime (verified via `ELECTRON_RUN_AS_NODE`). The sync
host resolves to two A records and TCP connect takes 320-360 ms from
the reporter's location, so every attempt is aborted. Current Node
ships a 500 ms default.

## Thread highlights (7 comments total)

- 2026-08-17 mrjo118 (COLLABORATOR): asks whether other clients get decent speed from the same server, and whether the issue also occurs on mobile
- 2026-08-17 PandaWood (NONE): argues 250 ms connect latency rules out most intercontinental server choices, and that the repro isolates the variable (same binary, same URL, only the timeout differs); mobile sync worked fine
- 2026-08-17 PandaWood (NONE): background: Node took 250 ms from RFC 8305 but uses it as an abort deadline, where the RFC uses it as the moment to start a parallel attempt
- 2026-08-17 mrjo118 (COLLABORATOR): made a code change updating the default to 500 ms to match Node 26, built a development Windows binary for testing (no way to test a slow TCP connection locally)
- 2026-08-18 PandaWood (NONE): offers to build the fix from the branch to test it

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: Joplin 3.7.10 (AppImage), CachyOS (Arch), KDE Plasma 6;
sync target WebDAV at app.koofr.net (resolves to 2 A records from
here); measured TCP connect time to the host: 320-360 ms across 20
attempts (`nping` samples in the report).

Steps:

1. `ELECTRON_RUN_AS_NODE=1 ./joplin -e 'console.log(require("net").getDefaultAutoSelectFamilyAttemptTimeout())'`
   prints `250`.
2. Triggered sync: fails with the issue's exact
   `FetchError ... Code: ETIMEDOUT` against `info.json`; the UI
   still reports "Synchronisation finished".
3. Control: same URL via `curl` from the same shell: 200 OK in under
   a second, every attempt.
4. Control: a 5-line fetch script on system Node 26.7.0 (default
   timeout 500 ms) against the same URL: succeeds on all 10 runs.
5. Control: the same script with
   `net.setDefaultAutoSelectFamilyAttemptTimeout(250)`: fails with
   ETIMEDOUT on 8 of 10 runs.

Expected: Joplin's bundled runtime tolerates connect latency above
250 ms, as current Node defaults do.

Actual: the 250 ms abort deadline reproduces the sync failure
deterministically, and raising it (control 4 vs 5) flips the outcome,
isolating the timeout as the variable.

## Candidate plan

### Diagnosis

Confirmed as reported: the bundled runtime's 250 ms
`autoSelectFamilyAttemptTimeout` aborts legitimate slow connects; the
control matrix isolates the timeout as the deciding variable.

### Proposed changes

1. Set the default `autoSelectFamilyAttemptTimeout` to 500 ms at app
   startup to match current Node (the direct fix).
2. While touching the network stack: replace `node-fetch` with
   `undici` across the desktop sync code, since node-fetch is in
   maintenance mode and undici handles Happy Eyeballs natively.
3. Add a Settings > Synchronisation panel field exposing the timeout
   for users on very slow links.
4. Fix the silent-success UI while in the area: sync failures should
   surface in the sync status instead of "Synchronisation finished"
   (the #12810 behavior the report mentions).
5. Add a retry-with-backoff wrapper around the sync target's fetch
   calls so transient connect aborts do not fail a whole sync pass.

### Files and areas

App startup (timeout default), `packages/lib` sync and WebDAV driver
(fetch replacement, retry wrapper), desktop Settings UI (new field),
sync status UI (error surfacing).

### Test plan

On the slow-connect setup, sync succeeds 10 of 10 runs after the
change; the new settings field round-trips; sync failures injected
via an unreachable host surface visibly in the UI.

## Candidate plan comment

I filed the isolation above (timeout matrix in the report) and want
to fix this properly. Beyond bumping the default to 500 ms, which
mrjo118's test build already tries, I plan to move the desktop sync
stack from node-fetch to undici, expose the timeout in Settings, make
sync failures visible in the UI, and wrap the sync fetches in
retry-with-backoff. That covers the whole failure surface this
uncovered rather than just the constant. Happy to split into a PR
series, starting with the undici migration.
