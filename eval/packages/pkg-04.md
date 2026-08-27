# Eval package: pkg-04

- source: junegunn/fzf#4260
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: junegunn/fzf (82558 stars, archived: no)
- description: A command-line fuzzy finder.
- latest release: v0.74.3 (2026-08-17)
- bug reports: template asks for OS, shell, confirmation the manual and existing issues were checked, and the problem with steps to reproduce
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### FZF appears to swallow key presses when used with `less` on Git Bash with ZSH on Windows (#4260)

opened by marovira (NONE) on 2025-02-19, state open, labels: bug, help-needed, windows

Steps: in Git Bash (or ZSH within Git Bash) on Windows, run
`echo "<file>" | fzf --bind="enter:execute(less {})"` and press enter
to select the file. The `less` prompt opens, but no key press reaches
it: j, k, Esc, Ctrl-d, Ctrl-c all do nothing, and the only way back to
the shell is to kill the `less` process.

If regular keys are pressed and `less` is then killed, the pressed
keys appear in fzf's prompt, which suggests fzf is swallowing the key
presses that should have gone to `less`. The issue is exclusive to
Windows; Linux does not present the problem.

## Thread highlights (11 comments total)

- 2025-02-19 marovira (NONE): first noticed via forgit (wfxr/forgit#423); diagnosis there pointed at fzf itself
- 2025-03-02 junegunn (OWNER): asks whether winpty is in use, for `$TERM_PROGRAM` values, and whether `MSYS=enable_pcon` changes anything
- 2025-03-03 junegunn (OWNER): reproduced on a Windows Server 2025 instance; found that `less` works when the execute command redirects with `> /dev/tty`, which non-Windows systems do not require
- 2025-03-03 junegunn (OWNER): "This seems to be the culprit", pointing at the console input handling in `src/tui/light_windows.go` (lines 70-84)
- 2025-03-03 junegunn (OWNER): posted a patched test binary from commit 8916cbc and asked the reporter to test it, noting it still consumes the first key for the execute program and that a proper fix for that part is not trivial
- 2025-03-03 marovira (NONE): the patched binary pretty much solves it; only the first key press is still swallowed

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: fzf 0.60.0 (choco), Git for Windows 2.47 (Git Bash,
MSYS2), Windows 11 23H2; also reproduced under ZSH 5.9 inside Git
Bash.

Steps:

1. `seq 1000 > test`
2. `echo test | fzf --bind 'enter:execute:less {}'`
3. Press enter; `less` opens showing the file.
4. Press j, k, q, Esc, Ctrl-d: no response; killed `less` from Task
   Manager; the pressed `jkq` then appeared in fzf's prompt line.

Control runs:

- Same steps on Ubuntu 24.04: `less` responds to every key.
- Same steps with the execute command written as
  `less {} > /dev/tty`: `less` responds normally on Windows.

Expected: keys reach `less` without a redirection workaround.

Actual: without the redirection, fzf's console input loop keeps
reading the keys on Windows, and `less` never sees them, matching the
issue.

## Candidate plan

Diagnosis: on Windows, fzf keeps reading console input while an
`execute` child runs, so an interactive child without an explicit
`/dev/tty` redirection never receives keys. The redirection control
run shows a reliable workaround exists today.

Scope: documentation only. In scope: the man page and the README
examples for `execute` bindings; a new FAQ entry. Not in scope: any
change to fzf's input handling code.

Approach:

1. Add a Windows note to the `execute` section of the man page: pipe
   interactive commands to the terminal with `> /dev/tty`.
2. Update the README's execute examples to include the redirection in
   a Windows-flagged variant.
3. Add a wiki FAQ entry describing the symptom (frozen pager, keys
   appearing in the fzf prompt afterwards) so searchers land on the
   workaround.

Test plan: on the Windows repro machine, follow only the new
documentation from a clean shell and confirm the documented command
form gives a fully interactive `less` (j, k, q all work); confirm the
docs build renders the new man page section.

## Candidate plan comment

Hi! I reproduced this on Windows 11 with fzf 0.60.0 (report above,
including the `> /dev/tty` control that behaves correctly). Since the
behavior has a reliable workaround, I plan to document it properly:
a Windows note in the man page's execute section, updated README
examples, and an FAQ entry describing the symptom. That should stop
people from losing sessions to a frozen pager. I can have the docs PR
up this week.
