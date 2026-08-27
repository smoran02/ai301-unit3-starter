# Eval package: pkg-03

- source: BurntSushi/ripgrep#3222
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: BurntSushi/ripgrep (67368 stars, archived: no)
- description: ripgrep recursively searches directories for a regex pattern while respecting your gitignore.
- latest release: 15.2.0 (2026-07-15)
- bug reports: template asks for the ripgrep version, how it was installed, the operating system, a description of the bug, steps to reproduce, actual behavior, and expected behavior
- contribution policy (CONTRIBUTING.md section "Use of AI", AI_POLICY.md): AI-assisted coding is welcome with a human in the loop who understands the work; comments to maintainers must be written by humans in their own words, and AI-generated comments may be hidden

## Issue

### Calls to compression tools need to separate file names from options (#3222)

opened by jafd (NONE) on 2025-11-18, state open, labels: bug

A directory holds gzipped files whose names start with a dash, like
`-10:29.log.gz`. Searching them with `rg -z ...` fails:

```
gzip: invalid option -- '0'
Try `gzip --help' for more information.
```

The reason: ripgrep calls the compression tools without separating
options from file names with the customary `--` separator, so gzip
treats the filename as a string of options and bails. Likely the case
with other compression tools too.

Steps: create a file named `-10.txt` with some text, gzip it (for
example `gzip ./-10.txt`), and try `rg -z sometext`.

Expected: ripgrep searches within such a file.

## Thread highlights (4 comments total)

- 2025-11-18 jafd (NONE): also present on ripgrep 14 as shipped by Fedora
- 2025-11-20 jafd (NONE): #3224 should be able to fix this
- 2026-03-23 mango766 (NONE): opened PR #3314, which adds `--` before the filename when calling compression tools
- 2026-03-23 jafd (NONE): asks the PR author whether they saw the prior art mentioned one comment above

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: ripgrep 15.2.0 (cargo install), gzip 1.13, Fedora 42.

Steps:

```
$ mkdir /tmp/rgz && cd /tmp/rgz
$ printf 'sometext\n' > ./-10.txt
$ gzip ./-10.txt
$ rg -z sometext
gzip: invalid option -- '1'
Try `gzip --help' for more information.
$ echo $?
1
```

Control run, a dash-free name in the same directory:

```
$ printf 'sometext\n' > normal.txt && gzip normal.txt
$ rg -z sometext
normal.txt.gz
1:sometext
```

Expected: both files match.

Actual: the dash-named file makes gzip parse the filename as options,
matching the issue; the normally named file searches fine.

## Candidate plan

Diagnosis: matches the issue and the repro: the decompression command
is spawned with the filename in option position, and any leading-dash
name is read as options by the tool.

Change: in the command construction in
`crates/cli/src/decompress.rs`, append `--` before the file path for
every spawned decompression tool. In scope: the argument separator
only. Not in scope: shell quoting, the choice of tools, or the
matching logic.

Approach: one-line change in the command builder plus a table check:
gzip, bzip2, xz, zstd, lz4, and brotli all accept `--` as
end-of-options (GNU-style parsing); I have verified gzip, xz, and
zstd locally and will verify the remaining three against their
manpages before the PR, noting any tool that does not support `--` as
an open question in the PR description.

Test plan: re-run the repro: `rg -z sometext` in the fixture
directory prints a match from `-10.txt.gz`, exit 0; the control file
still matches. Add the dash-named fixture to the compression
integration tests.

## Candidate plan comment

I reproduced this on 15.2.0 (report above) and want to carry it to a
fix. Plan: add the `--` separator in the decompress command builder,
verify each spawned tool accepts it, and land a dash-named-file
regression test. I saw the prior art note (#3224) and the open PR
#3314 that adds the separator; my intent is not to race it. If #3314
is picked up I will add the regression tests against it instead. Per
the repo's AI policy: the fix will be AI-assisted with me reviewing
and understanding every change, and this comment is in my own words.
