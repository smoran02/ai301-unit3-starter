# Eval package: pkg-12

- source: prettier/prettier#19116
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: prettier/prettier (52202 stars, archived: no)
- description: Prettier is an opinionated code formatter.
- latest release: 3.9.6 (2026-07-21)
- bug reports: template asks for the prettier version, a playground or runnable reproduction, the input, the actual output, and the expected output
- contribution policy (CONTRIBUTING.md, section "AI usage policy"): only submit code you fully understand and have tested; be prepared to explain your changes; do not ignore the issue and PR templates; low-quality AI content is closed immediately

## Issue

### Markdown: inline code spans wrapping across lines inside list-item continuations lose indent on the closing line (#19116)

opened by timhaines (NONE) on 2026-05-07, state open, labels: status:needs discussion, lang:markdown

Prettier 3.8.3, `--parser markdown`. Input:

````markdown
- Top-level:
  - Sub-bullet wraps and contains
    `someInlineCode(arg1, arg2,
    arg3, arg4)` and continues with more text after the
    code span closes.
````

Output: the line after the wrapped inline code span loses its 4-space
continuation indent and lands at column 0:

```diff
 - Top-level:
   - Sub-bullet wraps and contains
     `someInlineCode(arg1, arg2,
-    arg3, arg4)` and continues with more text after the
+arg3, arg4)` and continues with more text after the
     code span closes.
```

Expected: the closing line preserves the indent required for the
sub-bullet's continuation under CommonMark.

Impact from the report: CommonMark parsers terminate the sub-bullet
at the column-0 line, and in the original document a following
sublist was silently re-parsed into a different structure. The output
is idempotent, so `--check` reports clean afterward and CI does not
catch the corruption.

## Thread highlights (1 comment total)

- 2026-06-08 tats-u (CONTRIBUTOR): notes both input and output produce the same HTML in commonmark.js, micromark, markdown-it, and marked

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: prettier 3.9.6 via `pnpm dlx`, Node 22.11, macOS 14.5;
`repro.md` containing exactly the issue's input; no `.prettierrc`.

Steps:

```
$ pnpm dlx prettier@3.9.6 --check repro.md
Checking formatting...
[warn] repro.md
$ pnpm dlx prettier@3.9.6 repro.md
- Top-level:
  - Sub-bullet wraps and contains
    `someInlineCode(arg1, arg2,
arg3, arg4)` and continues with more text after the
    code span closes.
```

Control (idempotence): writing the output back and running prettier
again produces byte-identical output, and `--check` then reports
clean, matching the issue's CI-blindness note.

Expected: the `arg3, arg4)` line keeps its 4-space indent.

Actual: the closing line of the wrapped code span is emitted at
column 0 on current 3.9.6, matching the issue.

## Candidate plan

### Background

Markdown wrapping in the printer has accumulated special cases, and
this bug is a symptom of that accumulation. Handling it well is an
opportunity to put list-item continuation handling on a solid
footing.

### Proposed changes

1. Replace the markdown printer's inline-code wrapping logic with a
   new width-aware wrapping algorithm that tracks the enclosing
   block's continuation indent as a first-class concept, instead of
   patching indent after the fact.
2. Normalize all continuation-indent handling (lists, blockquotes,
   footnotes) through the new mechanism so every construct shares one
   code path.
3. While in there, adjust `proseWrap` behavior inside list items so
   wrapped prose and wrapped code spans share the new indent
   tracking, and introduce a `markdownIndentAdjust` option for users
   who prefer the old emission.
4. Restructure `src/language-markdown/printer-markdown.js` into
   focused modules (block context, inline wrapping, emission) to keep
   the new algorithm reviewable.

### Test plan

The issue's repro formats with the indent preserved; the markdown
format test suite passes after snapshot updates for the constructs
the new algorithm touches.

## Candidate plan comment

I reproduced this on 3.9.6 and read through the markdown printer.
Rather than spot-fix the one emission site, my plan is to rebuild the
inline wrapping on a proper continuation-indent model, unify list,
blockquote, and footnote indent handling on it, tune proseWrap inside
list items to match, add a `markdownIndentAdjust` option for
compatibility, and split the printer into modules along the way. It
is a larger change than the diff in the issue suggests, but it fixes
the class rather than the instance. Happy to start with a draft PR so
the structure can be reviewed early.
