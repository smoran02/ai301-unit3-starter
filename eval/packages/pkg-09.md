# Eval package: pkg-09

- source: sharkdp/fd#2067
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: sharkdp/fd (44120 stars, archived: no)
- description: A simple, fast and user-friendly alternative to 'find'.
- latest release: v10.4.2 (2026-03-10)
- bug reports: template asks reporters to confirm they read the troubleshooting section, describe the bug and the expected behavior, and give their fd version and operating system
- contribution policy (CONTRIBUTING.md, pull-request guidelines): AI-assisted code contributions are accepted from contributors who understand the code and must state the tool and the extent of its use in the pull request; comments to maintainers are expected to be in the contributor's own words and voice (AI help with grammar, spelling, and proofreading is fine); the policy states no disclosure ask for issue comments

## Issue

### --glob patterns with a path separator never match in --full-path mode on native Windows (#2067)

opened by Hotragn (NONE) on 2026-07-22, state open, labels: bug, upstream-feature

On native Windows (PowerShell or cmd, no MSYS involved), glob
patterns that contain a path separator never match anything in
`--full-path` mode. Repro on fd 10.4.2, Windows 11:

```
mkdir C:\t\fixture\src\foo
echo x > C:\t\fixture\src\foo\a.spec.ts
fd --glob --full-path "**/src/**/*.spec.ts" C:\t\fixture      -> no output, exit 0
fd --glob --full-path "**\src\**\*.spec.ts" C:\t\fixture      -> no output
fd --full-path "src[/\\].*\.spec\.ts$" C:\t\fixture           -> matches (regex mode)
```

The regex-mode line shows the candidate paths still contain
backslashes at match time, while the glob-derived regex only accepts
`/`. Cause per the report: in glob mode `build_pattern_regex`
(src/main.rs) extracts the regex from globset with `/` as the literal
separator, and walk.rs then matches that regex against the raw native
path bytes; globset's own matcher normalizes `\` to `/` in
`Candidate::new` before matching, but that step is skipped when the
extracted regex is used directly.

## Thread highlights (6 comments total)

- 2026-07-23 tmccombs (COLLABORATOR): this seems to be a limitation of globset, which assumes `/` as the separator
- 2026-07-23 tmccombs (COLLABORATOR): lists three fix options: (1) match with the glob directly instead of converting to a regex (#1606 has an implementation), (2) normalize the path to use `/` instead of `\` for the comparison, which could simplify other code paths, (3) a third variant a contributor has since implemented
- 2026-08-04 petrroll (NONE): offers option 2 as the simpler and less regex-fragile route, in PR #2089; notes globset already does the same normalization internally, and that ripgrep matches via `Candidate::new` which normalizes the same way

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: fd 10.4.2 (winget), Windows 11 23H2, PowerShell 7.4
(native console, no MSYS or WSL in the loop).

Steps:

1. `mkdir C:\t\fixture\src\foo; echo x > C:\t\fixture\src\foo\a.spec.ts`
2. `fd --glob --full-path "**/src/**/*.spec.ts" C:\t\fixture`
   prints nothing, exit 0.
3. `fd --glob --full-path "**\src\**\*.spec.ts" C:\t\fixture`
   prints nothing.
4. Control (regex mode): `fd --full-path "src[/\\].*\.spec\.ts$" C:\t\fixture`
   prints `C:\t\fixture\src\foo\a.spec.ts`.
5. Control (Linux, same fixture layout under /tmp): the step-2
   command form matches.

Expected: step 2 matches the fixture file on Windows as it does on
Linux.

Actual: glob-with-separator patterns match nothing in full-path mode
on native Windows, while regex mode over the same paths matches,
confirming the candidates carry backslashes at match time.

## Candidate plan

Diagnosis: as the issue and my controls show, the glob-derived regex
expects `/` separators but is matched against raw native paths with
`\`, because the normalization globset would do in `Candidate::new`
is skipped when the extracted regex is used directly.

Change: normalize path separators for the match candidate: where
walk.rs matches the pattern regex against the full path in
`--full-path` glob mode on Windows, map `\` to `/` in the candidate
bytes first (option 2 from the thread, which the collaborator noted
is the simpler route and globset already does internally). In scope:
the glob-mode full-path match path on Windows. Not in scope, stated
deferrals: option 1 (switching to direct globset matching, a larger
rework the maintainers may prefer long term), and any change to
regex-mode matching, which is correct today. The normalized bytes are
used only for matching, never for output, so printed paths keep
native separators.

Files: `src/walk.rs` (candidate normalization at the match site),
`src/main.rs` (no change expected to `build_pattern_regex`; noted for
review), `tests/tests.rs` (Windows-gated fixture test).

Test plan: on the Windows fixture, the three pattern spellings from
the repro (steps 2 and 3 plus the double-backslash form) each print
`C:\t\fixture\src\foo\a.spec.ts`; the regex-mode control stays
unchanged; the Linux control still matches (no behavior change where
`\` cannot be a separator).

Risk: `\` is a legal filename character on Unix; the normalization is
therefore gated to Windows targets only, and I call that out for
review since it is the one place this change could alter matches.

## Candidate plan comment

I hit this on a native Windows setup and reproduced it cleanly
(report above, including the regex-mode control showing backslashes
at match time). I would like to implement option 2 from the
discussion here: normalize the match candidate to `/` on Windows at
the walk.rs match site, Windows-gated, with fixture tests for the
three pattern spellings. I have read PR #2089, which takes the same
route; if that lands first I will rebase my tests onto it rather than
duplicate the change. Deliberately not touching option 1's direct
globset matching; that is a bigger rework than this bug needs.
