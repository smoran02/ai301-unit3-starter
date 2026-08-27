# Eval package: pkg-08

- source: jqlang/jq#3538
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: jqlang/jq (35458 stars, archived: no)
- description: Command-line JSON processor.
- latest release: jq-1.8.2 (2026-06-20)
- bug reports: template asks reporters to describe the bug, provide reproduction steps, expected behavior, and environment (OS and jq version)
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### Inconsistent delpaths behavior with negative indices (#3538)

opened by cscott (NONE) on 2026-05-04, state open, labels: bug

jq reconciles positive and negative indices and executes all
deletions as if simultaneous, as demonstrated in `jq.test` around
line 1184, but only when they occur in the leaves of the path.
Negative indices in non-leaf nodes are not collected together, so the
results differ, as if deletions on negative indices are evaluated
first and the positive-index deletions then run on the shortened
array.

```
$ echo '[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]' | jq -c 'del(.[-6],.[6])'
[0,1,2,3,5,7,8,9]
$ echo '[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]' | jq -c 'del(.[0][-6],.[-1][6])'
[[0,1,2,4,5,7,8,9]]
$ echo '[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]' | jq -c 'del(.[-1][-6],.[0][6])'
[[0,1,2,3,5,6,8,9]]
```

The single-level case deletes elements 4 and 6 (simultaneous
semantics); the mixed non-leaf cases behave as if one deletion ran
before the other. The same behavior is evident in `delpaths`.

## Thread highlights (3 comments total)

- 2026-07-02 maximilize (NONE): two open PRs target this, #3543 and #3548; #3543 fixes all reported cases; root cause is `delpaths_sorted` (src/jv_aux.c:473-484) grouping paths that share a key only by adjacency in the sorted order, which mixed-sign non-leaf indices break
- 2026-07-04 cscott (NONE): describes an alternative tombstone approach used in another implementation: mark deleted slots, compact at the end, no sorting subtleties
- 2026-07-04 maximilize (NONE): agrees the tombstone shape is the more robust rework if someone takes on delpaths_sorted; short of that, #3543 and #3548 are the concrete patches on the table

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: jq built from master at 1.8.2 tag (autotools build, gcc
14), Ubuntu 24.04.

Steps and output:

```
$ echo '[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]' | ./jq -c 'del(.[-6],.[6])'
[0,1,2,3,5,7,8,9]
$ echo '[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]' | ./jq -c 'del(.[0][-6],.[-1][6])'
[[0,1,2,4,5,7,8,9]]
$ echo '[[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]]' | ./jq -c 'del(.[-1][-6],.[0][6])'
[[0,1,2,3,5,6,8,9]]
```

Control: the all-positive and all-negative two-level variants both
print `[[0,1,2,3,5,7,8,9]]`, matching the single-level semantics.

Expected: all three commands delete elements 4 and 6 of the inner
array (simultaneous semantics), as the leaf-level case does.

Actual: the mixed-sign non-leaf cases each delete a different wrong
pair, matching the issue's sequential-evaluation description.

## Candidate plan

Diagnosis: matches the thread's analysis, confirmed by the repro
controls: `delpaths_sorted` (src/jv_aux.c, lines 473-484) groups
paths sharing a key at the current level by adjacency in sorted
order, and mixed-sign indices at non-leaf levels sort apart, so the
group splits and the deletions run sequentially.

Change, one fix: normalize negative indices against the array length
at each level before grouping (the same reconciliation the leaf level
already gets), so equivalent indices group together regardless of
sign. In scope: the grouping in `delpaths_sorted`. Not in scope: the
tombstone rework discussed in the thread; it is the better long-term
shape but a larger change, and I am deliberately deferring it.

Files: `src/jv_aux.c` (delpaths_sorted), `tests/jq.test` (the issue's
three cases plus the two controls as regression tests).

Test plan: the three repro commands print `[[0,1,2,3,5,7,8,9]]` (or
its single-level equivalent), the two controls stay unchanged, and
the existing jq.test suite passes, in particular the simultaneous-
deletion case around line 1184.

Risk: out-of-range negative indices at non-leaf levels; I will match
whatever the leaf level does for those today and add a test pinning
that behavior.

## Candidate plan comment

I reproduced all three cases against master (report above). My plan
is the bounded version of what this thread already converged on:
normalize negative indices before grouping in `delpaths_sorted`, add
the issue's cases to jq.test, and leave the tombstone rework for a
separate effort. I have read #3543 and #3548; if the maintainers
prefer landing one of those, I am happy to contribute the regression
tests to it instead of a third patch.
