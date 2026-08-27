# Eval package: pkg-16

- source: pandas-dev/pandas#57666
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: pandas-dev/pandas (49511 stars, archived: no)
- description: Flexible and powerful data analysis / manipulation library for Python, providing labeled data structures similar to R data.frame objects, statistical functions, and much more.
- latest release: v3.0.5 (2026-07-22)
- bug reports: template asks reporters to confirm the bug exists on the latest version and on the main branch, and to provide a reproducible example, an issue description, the expected behavior, and the output of `pd.show_versions()`
- contribution policy (CONTRIBUTING.md): standard contribution guide; no stated AI policy

## Issue

### BUG: pyarrow read_csv engine stripping leading zeros with dtype=str (#57666)

opened by dadrake3 (NONE) on 2024-02-28, state open, labels: Bug, IO CSV, Arrow

With `engine="pyarrow"` and `dtype=str`, leading zeros in numeric-
looking columns are removed even though the resulting column type is
object. The python engine keeps them.

```python
df_arrow = pd.read_csv(StringIO(x), delimiter="|", header=None,
                       dtype=str, engine="pyarrow",
                       keep_default_na=False)
```

For input rows like `AB|000388907|abc|0150`, the pyarrow engine
yields `388907` and `150`; the python engine yields `000388907` and
`0150` as expected.

Expected: when treating all columns as strings, leading zeros are
retained and the data is unmodified.

## Thread highlights (14 comments total)

- 2024-03-15 mroeschke (MEMBER): asks whether pyarrow's own `pyarrow.csv.read_csv` shows the same result
- 2024-03-15 benjaminbauer (NONE): matrix test: pandas python engine keeps `01`, pandas pyarrow engine strips to `1`, pyarrow native `csv.read_csv` keeps `01`
- 2024-03-23 jorisvandenbossche (MEMBER): explains the cause: the `dtype` argument is handled only as post-processing; pandas lets pyarrow read the CSV with type inference (numeric here) and afterwards casts the result to the requested dtype, which is why the zeros are lost
- 2025-07-03 dxdc (NONE): still present with pyarrow 20 / pandas 2.3
- 2025-07-04 dxdc (NONE): sketches the fix direction: map `dtype` into pyarrow's `column_types` in `_get_pyarrow_options` so pyarrow parses the columns as strings in the first place

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: pandas 3.0.5, pyarrow 21.0, Python 3.12, Ubuntu 24.04.

Steps (single-column matrix, value `01`):

1. pandas, `engine="python"`, `dtype=str`: value reads as `"01"`.
2. pandas, `engine="pyarrow"`, `dtype=str`: value reads as `"1"`.
3. pyarrow native, `pa.csv.read_csv` with
   `convert_options=ConvertOptions(column_types={"a": pa.string()})`:
   value reads as `"01"`.
4. pyarrow native with no `column_types` (inference on): the table's
   column arrives as `int64` with value `1`; the zeros are already
   gone in the parsed table, before any cast to string could run.

Expected: step 2 matches steps 1 and 3.

Actual: only the pandas pyarrow engine strips the zeros. Step 4
pins where they disappear: during pyarrow's typed parse under
inference, not afterward; pyarrow itself preserves them whenever it
is told to parse the column as string (step 3), matching the member's
explanation in the thread.

## Candidate plan

### Diagnosis

The defect is in the pandas-side cast that runs after pyarrow returns
its table. `ArrowParserWrapper._finalize_pandas_output` casts the
inferred numeric columns to the requested `dtype=str` using a plain
`astype`, and Python's integer-to-string formatting emits `388907`
without its original zeros. The cast is where the data is damaged, so
the cast is what must change.

### Scope

In scope: the post-read cast in
`pandas/io/parsers/arrow_parser_wrapper.py`. Not in scope: pyarrow's
reader options or the python engine.

### Files

- `pandas/io/parsers/arrow_parser_wrapper.py`
  (`_finalize_pandas_output`)
- `pandas/tests/io/parser/test_read_fwf.py` area tests for dtype=str

### Approach

Replace the plain `astype(str)` with a zero-preserving string
formatter: when the requested dtype is string and the inferred column
is integer, re-pad the rendered strings to the column's original
width so `388907` renders as `000388907` again. Width can be
recovered from the maximum digit count of the column plus the pad the
CSV used.

### Test plan

The issue's four-row example matches the python engine's output; the
parser test suite passes for the pyarrow engine.

## Candidate plan comment

I worked through this one end to end (matrix in my report). The
damage happens in the pandas post-read cast, so my plan is to make
`_finalize_pandas_output` cast integer columns to strings with a
zero-preserving formatter that restores the original column width,
matching the python engine's output on the issue's example. It is
contained to the arrow parser wrapper and comes with parser tests.
I'll open the PR once the suite is green.
