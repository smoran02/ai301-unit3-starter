# Eval package: pkg-18

- source: golangci/golangci-lint#6467
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: golangci/golangci-lint (19263 stars, archived: no)
- description: Fast linters runner for Go.
- latest release: v2.12.2 (2026-05-06)
- bug reports: template asks reporters to confirm they use a binary release within the 2 latest major releases, searched existing issues, read the typecheck FAQ, and tried the standalone linter, then to provide a problem description, the golangci-lint version, the configuration, the Go environment, and a code example
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### sqlclosecheck|rowserrcheck: panic unreachable (#6467)

opened by erane-opti (NONE) on 2026-03-29, state open, labels: bug, dependencies

Both linters call `go/types.Identical(..)` which panics with
`unreachable`. The reporter suspects (not sure) the function cannot
handle `iter.Seq2`.

Version: golangci-lint 2.11.4 built with go1.26.1; project on
go1.25.8. Configuration: `golangci-lint run --enable sqlclosecheck
--disable errcheck` (same with rowserrcheck).

## Thread highlights (3 comments total)

- 2026-03-29 ldez (MEMBER): the problem is not iter.Seq2 itself but using `defer` inside a `for`; includes a reduced example; such defer usage does not work as expected and should not be written that way
- 2026-03-29 erane-opti (NONE): confirms the trigger was switching from ranging over a map to ranging over `iter.Seq2`, with a `defer x.Close()` in the loop body; both linters work without the defer
- 2026-03-29 ldez (MEMBER): opened PRs on the two upstream linters to fix the bug (sqlclosecheck#50, rowserrcheck#34); golangci-lint now uses a fork of rowserrcheck

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: golangci-lint 2.11.4 (official binary), go 1.25.8,
Ubuntu 24.04; fresh module with one file.

Steps:

1. Wrote a minimal package ranging over an `iter.Seq2` of `*sql.DB`
   with `defer rows.Close()` inside the loop body (shape of the
   member's reduced example).
2. `golangci-lint run --enable rowserrcheck --disable errcheck`:

```
panic: unreachable
goroutine 1 [running]:
go/types.(*Checker).identical(...)
        go/types/predicates.go:...
github.com/jingyugao/rowserrcheck/passes/rowserr.(*runner).run(...)
```

3. Same command with `--enable sqlclosecheck`: same panic, different
   linter frame.
4. Control: moving the `defer` out of the loop body (or replacing the
   iterator range with a slice range): both linters complete cleanly
   with findings as expected.

Expected: a lint finding (or clean pass), never a panic.

Actual: both linters panic inside `go/types.Identical` on the
iterator-range-plus-defer shape, matching the issue.

## Candidate plan

A linter runner should never crash on valid code, so the plan is to
make the panic go away.

Steps:

1. Add a recover() safety net somewhere around linter execution so a
   panicking analyzer reports an error instead of crashing the whole
   run.
2. Look into how the two linters handle iter.Seq2 and fix the type
   logic, either upstream or in the vendored copies, whichever turns
   out to be easier.
3. Maybe also check other linters for the same pattern while at it.

Test plan: golangci-lint should not panic on the reproduction
anymore.

## Candidate plan comment

Hit this on our codebase and reduced it (report above). I'd like to
fix it: my plan is to add panic recovery around linter execution and
then sort out the iter.Seq2 handling in the two linters, upstream or
vendored as needed. Might also scan the other bundled linters for
similar crashes. Will report back when the panic is gone.
