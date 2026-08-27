# Eval package: calib-04

- source: BurntSushi/ripgrep#3070
- captured: 2026-08-18
- calibration: true

## Repo facts (captured 2026-08-18)

- repo: BurntSushi/ripgrep (67368 stars, archived: no)
- description: ripgrep recursively searches directories for a regex pattern while respecting your gitignore.
- latest release: 15.2.0 (2026-07-15)
- bug reports: template asks for the ripgrep version, how it was installed, the operating system, a description of the bug, steps to reproduce, actual behavior, and expected behavior
- contribution policy (CONTRIBUTING.md section "Use of AI", AI_POLICY.md): AI-assisted coding is welcome with a human in the loop who understands the work; comments to maintainers must be written by humans in their own words, and AI-generated comments may be hidden

## Issue

### Commands that use glob filters with absolute paths behave differently depending on cwd (#3070)

opened by mattalxndr (NONE) on 2025-06-20, state open, labels: bug

ripgrep 14.1.1, Arch Linux. Steps:

```
 ~ % mkdir /tmp/rg
 ~ % echo 1 > /tmp/rg/one.txt
 ~ % echo 2 > /tmp/rg/two.txt
 / % rg --glob='!/tmp/rg/two.txt' . /tmp/rg/
/tmp/rg/one.txt
1:1
 /tmp/rg % rg --glob='!/tmp/rg/two.txt' . /tmp/rg/
/tmp/rg/one.txt
1:1

/tmp/rg/two.txt
1:2
```

The same command excludes `two.txt` when run from `/` but not when
run from `/tmp/rg`.

## Thread highlights (3 comments total)

- 2025-06-20 BurntSushi (OWNER): ripgrep does not really have a way to filter on absolute paths; it is a limitation of the gitignore paradigm, and `-g/--glob` is documented to behave like gitignore; working as intended, though counter-intuitive, and ripgrep probably should have a better way to approach the problem
- 2025-10-16 BurntSushi (OWNER): looked into whether there is an easy fix, figured out the problem, but "the fix is hard": the `ignore` crate did not carefully consider how filtering interacts with the current working directory when patterns are matched relative to different roots

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: ripgrep 15.2.0 (pacman), Arch Linux.

Steps:

```
$ mkdir /tmp/rgt && echo 1 > /tmp/rgt/one.txt && echo 2 > /tmp/rgt/two.txt
$ cd / && rg --glob='!/tmp/rgt/two.txt' . /tmp/rgt/
/tmp/rgt/one.txt
1:1
$ cd /tmp/rgt && rg --glob='!/tmp/rgt/two.txt' . /tmp/rgt/
/tmp/rgt/one.txt
1:1

/tmp/rgt/two.txt
1:2
```

Control: a relative glob (`--glob='!two.txt'`) excludes the file from
both working directories.

Expected: the absolute-path glob behaves the same regardless of cwd.

Actual: the exclusion holds from `/` and silently stops holding from
inside the directory, matching the issue on current 15.2.0.

## Candidate plan

### Diagnosis

Grounded in the owner's analysis in the thread: `-g` patterns are
matched gitignore-style relative to a root that shifts with the
working directory, so a pattern written as an absolute path only
lines up with candidate paths from some cwds.

### Scope

One bounded change: patterns that begin with `/` and name an existing
absolute path are normalized at flag-processing time to be relative
to the search root they fall under, so they match identically from
any cwd. In scope: the glob preprocessing in
`crates/core/flags/hiargs.rs` where override globs are built, and the
override builder setup in the `ignore` crate consumer. Not in scope:
general gitignore semantics, config-file globs, or the `ignore`
crate's internal matching, per the owner's note that the deep fix is
hard; this is the narrow absolute-prefix case only, and I would
present it as opt-in behavior for review given the documented
gitignore semantics.

### Approach

1. At override-build time, detect `-g` patterns starting with `/`
   that resolve under a provided search path; rewrite them relative
   to that search path.
2. Leave every other pattern untouched.
3. Document the normalization in the `-g` flag docs.

### Test plan

Run the full test suite (`cargo test --workspace`) and make sure
nothing regresses.

## Candidate plan comment

I read the discussion here, including the note that the deep fix in
the ignore crate is hard: this proposal deliberately stays out of the
crate and only normalizes the narrow absolute-path-prefix case at
flag time, presented as a behavior change for the maintainers to
accept or reject given the documented gitignore semantics. The plan
names the exact preprocessing site and stays one bounded change. Per
the repo's AI policy: the implementation will be AI-assisted with me
reviewing every change, and this comment is in my own words.
