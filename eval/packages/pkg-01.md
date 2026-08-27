# Eval package: pkg-01

- source: httpie/cli#1838
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: httpie/cli (38430 stars, archived: no)
- description: Modern, user-friendly command-line HTTP client for the API era. JSON support, colors, sessions, downloads.
- latest release: 3.2.4 (2024-11-01)
- bug reports: template asks reporters to confirm they searched for similar issues and are on the latest version, and to provide minimal reproduction steps
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Inconsistent argument parsing behavior across Python versions (< 3.13 vs 3.13+) (#1838)

opened by Im-Siyoun (NONE) on 2026-04-30, state open, labels: bug, new

The position of optional flags (like `-v`) affects argument parsing
differently depending on the Python version. This is due to
improvements in Python 3.13's argparse module, but it creates an
inconsistent user experience for users on Python 3.11/3.12 (still
officially supported until 2027-2028).

Test case 1: `-v` flag after URL (fails on Python 3.11-3.12, works on
3.13+):

```
$ http --offline --ignore-stdin post pie.dev/post -v 'header1:xyz' x=1
```

On Python 3.11 and 3.12 this prints:

```
usage:
    http [METHOD] URL [REQUEST_ITEM ...]

error:
    unrecognized arguments: header1:xyz x=1
```

On Python 3.13.5 and higher the same command prints the full request
with `header1: xyz` and `{"x": "1"}` as expected.

Test case 2: `-v` before the URL fails on all versions tested.

Expected: the command should work consistently across all supported
Python versions, regardless of where optional flags are placed.

## Thread highlights (4 comments total)

- 2026-05-01 Im-Siyoun (NONE): if this is an argparse limitation or intended behavior, clearer documentation or better error messaging may still help users on Python below 3.13
- 2026-06-12 rupayon123 (NONE): tried clean virtualenvs with PyPI httpie 3.2.4; on their machine the post-URL variant succeeded on Python 3.12.13 and 3.14.5, while the pre-URL variant failed on both; results may vary by argparse point release

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: HTTPie 3.2.4 (pip), macOS 14.5 (arm64); Python 3.11.15
and 3.13.5 side by side via pyenv virtualenvs.

Steps:

1. In the 3.11.15 venv:

```
$ http --offline --ignore-stdin post pie.dev/post -v 'header1:xyz' x=1
usage:
    http [METHOD] URL [REQUEST_ITEM ...]

error:
    unrecognized arguments: header1:xyz x=1
$ echo $?
2
```

2. Control run, same venv, same items, no `-v` flag:

```
$ http --offline --ignore-stdin post pie.dev/post 'header1:xyz' x=1
POST /post HTTP/1.1
...
header1: xyz

{"x": "1"}
```

3. Same command as step 1 in the 3.13.5 venv: prints the full request,
   exit 0.

4. `--debug` on the failing run shows the error is raised by
   argparse's `parse_args` while consuming positionals; the request
   items are never handed to HTTPie's item parser.

Expected: step 1 behaves like step 3 on every supported Python.

Actual: with exactly one trailing flag between the URL and the request
items, Python 3.11/3.12 argparse stops consuming positionals and
reports them unrecognized; the same items parse fine without the flag
(step 2) and on 3.13 (step 3).

## Candidate plan

### Diagnosis

The `REQUEST_ITEM` tokenizer in `httpie/cli/requestitems.py` is the
problem. Its separator regex fails to recognize `header1:xyz` and
`x=1` as valid items when an optional flag appears earlier in the
argument list, so the items fall through as unrecognized arguments.
The Python-version difference is a red herring; the tokenizer has
always been too strict about colon items.

### Scope

In scope: rewrite the request-item tokenizer's separator matching so
colon and equals items are recognized regardless of surrounding flags.
Not in scope: argparse itself, flag handling, docs.

### Files

- `httpie/cli/requestitems.py` (the item tokenizer and its regex)
- `tests/test_cli.py` (new tokenizer cases)

### Approach

1. Extend the item-separator regex to accept item tokens that follow
   an optional flag.
2. Add tokenizer unit tests for `header1:xyz` and `x=1` in
   flag-adjacent positions.

### Test plan

Re-run the issue's test case 1 on Python 3.11: after the tokenizer
fix, the request prints with `header1: xyz` present, exit 0. Run the
tokenizer unit tests on 3.11, 3.12, and 3.13.

## Candidate plan comment

I dug into this and the root cause is httpie's own request-item
tokenizer being too strict, not argparse: I plan to rewrite the
separator matching in `requestitems.py` so colon and equals items
parse regardless of flag position, with tests across 3.11-3.13. The
version difference in the report is a side effect. I'll have a PR up
once the tokenizer tests pass.
