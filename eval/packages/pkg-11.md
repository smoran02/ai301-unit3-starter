# Eval package: pkg-11

- source: mikefarah/yq#2782
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: mikefarah/yq (15846 stars, archived: no)
- description: yq is a portable command-line YAML, JSON, XML, CSV, TOML, HCL and properties processor.
- latest release: v4.53.3 (2026-06-06)
- bug reports: template asks for the yq version, operating system, how yq was installed, a concise input document (10 lines or less), the command run, actual behavior, and expected behavior
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Missing keys are dropped from [...] inside select/and/or (#2782)

opened by johejo (NONE) on 2026-07-19, state open, labels: bug, v4

Collecting a missing key into an array normally produces `[null]`,
but inside a select/and/or condition the missing key is dropped.

Version of yq: 4.53.3, macOS, built from source.

```
yq -n '{} | ([.a] | length)'                    # 1 (ok)
yq -n '{} | select([.a] | length == 1)'         # no output (expected {})
yq -n '{} | (true and ([.a] | length == 1))'    # false (expected true)
```

Expected: `[.a]` should be `[null]` (length 1) everywhere, as it is
at the top level (and as in jq).

## Thread highlights (1 comment total)

- 2026-08-16 vjymisal0 (NONE): the two cases differ because of `DontAutoCreate`: `[...]` (collectOperator) evaluates its RHS in `context.SingleChildContext`, but select, and, or evaluate their condition in `context.SingleReadonlyChildContext`, which sets `DontAutoCreate`; `traverseMap` only synthesizes the missing key when that flag is clear

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: yq 4.53.3 (Homebrew), macOS 14.5.

Steps and output:

```
$ yq -n '{} | ([.a] | length)'
1
$ yq -n '{} | select([.a] | length == 1)'
$ yq -n '{} | select([.a] | length == 1)' | wc -c
       0
$ yq -n '{} | (true and ([.a] | length == 1))'
false
```

Control: the top-level collect (first command) produces `[null]`
(length 1) exactly as documented; only the select/and/or contexts
drop the missing key.

Expected: `{}` from the select, `true` from the and.

Actual: empty output and `false`, matching the issue: the same
collect expression behaves differently inside a condition context.

## Candidate plan

### Diagnosis

The collect operator is the defect: `[...]` fails to synthesize a
null entry for a missing key, producing an empty array instead of
`[null]`. That makes `length == 1` false, which is exactly what the
select and and cases show.

### Scope

In scope: the collect operator. Not in scope: select, and, or, which
are just consumers of the collected value.

### Files

- `pkg/yqlib/operator_collect.go` (the collect operator)
- `pkg/yqlib/operator_collect_test.go` (new cases)

### Approach

Change the collect operator so that traversing a missing key always
contributes a null element to the collected array, regardless of
where the collect appears. Add scenarios for `[.a]` over `{}` inside
and outside conditions.

### Test plan

The issue's three commands return `1`, `{}`, and `true`
respectively; the collect operator test suite passes.

## Candidate plan comment

Investigated this: the collect operator `[...]` is dropping the
missing key instead of collecting a null, which breaks any length
test built on it. My plan is to fix collect so a missing key always
contributes null to the array, with the issue's three commands as
regression scenarios. Should be contained to the collect operator
file. Will report back with the PR.
