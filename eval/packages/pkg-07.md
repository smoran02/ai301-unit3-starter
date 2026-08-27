# Eval package: pkg-07

- source: processing/p5.js#8930
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: processing/p5.js (23881 stars, archived: no)
- description: p5.js is a client-side JS platform that empowers artists, designers, students, and anyone to learn to code and express themselves creatively on the web.
- latest release: v2.3.2 (2026-07-30)
- bug reports: template asks for the p5.js version, operating system, web browser and version, actual behavior, expected behavior, and steps to reproduce with a snippet
- contribution policy (CONTRIBUTING.md, section "AI Usage Policy"): fully AI-generated contributions are not accepted; assistive AI use is allowed, and the contributor must understand and take responsibility for every change (details in AI_USAGE_POLICY.md)

## Issue

### [p5.js 2.0+ Bug Report]: Some Vector friendly errors don't work correctly (#8930)

opened by sidwellr (NONE) on 2026-06-16, state open, labels: Bug, Area:Math, p5.js 2.0+, Reserved (CodeDay)

p5.js version 2.3.0, sub-area Math.

Steps:

1. Run the snippet below. It has an error; the first param should be
   a vector.
2. The expected output is a friendly error message "The v1 parameter
   should be of type Array or p5.Vector".
3. Instead, it gives an error "TypeError: this._friendlyError is not
   a function".

```js
function setup() {
  print(p5.Vector.equals(1, createVector(1, 2)));
}
```

Discussion from the report: friendly errors for vectors seem to work
fine for instance methods like `setValue()`, but not for static
methods like `p5.Vector.equals`.

## Thread highlights (11 comments total)

- 2026-06-17 BHARATH0153 (NONE): cause analysis: static methods like `p5.Vector.equals()` call `this._friendlyError` where `this` is the Vector constructor, but `_friendlyError` is only set on `Vector.prototype`, not on Vector itself; suggests also overriding the static `friendlyErrorsDisabled` check
- 2026-06-29 ksen0 (MEMBER): the issue has been added to the CodeDay tasks; contributors welcome to help review and test solutions

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: p5.js 2.3.0 (unminified CDN build, p5.js not p5.min.js),
Chromium 138, Linux Mint 22.1; p5.js Web Editor sketch.

Steps:

1. Sketch calls `p5.Vector.equals(1, createVector(1, 2))` in
   `setup()`.
2. Console shows `TypeError: this._friendlyError is not a function`
   raised from the static `equals` path. No friendly error prints.
3. Control run, same sketch and same build: an instance-method misuse
   (`createVector(1, 2).equals(1)` style parameter error) prints the
   friendly error message as expected ("The v1 parameter should be of
   type..." form), confirming the friendly error system is present
   and active in this build.
4. Second control: `p5.disableFriendlyErrors` is false (checked in
   console).

Expected: the static call path prints the same friendly parameter
error as the instance path.

Actual: instance methods produce friendly errors; static methods
throw `TypeError: this._friendlyError is not a function`, matching
the issue.

## Candidate plan

### Diagnosis

The friendly error system (FES) is not present in the 2.x browser
bundles. The 2.0 build pipeline moved to a new bundler configuration,
and the FES module is being tree-shaken out of the published builds,
which is why `this._friendlyError` does not exist at the call site.
The TypeError is the tell: the function is simply absent from the
bundle.

### Scope

In scope: the build configuration. Not in scope: the Vector class or
the FES module code, which are fine as written.

### Files

- `rollup.config.mjs` (bundle entries and treeshake options)
- `package.json` build scripts

### Approach

1. Mark the FES module as having side effects so the bundler keeps
   its registration code in the published builds.
2. Add a bundle-content CI assertion that the published p5.js build
   contains the FES registration.

### Test plan

Build the bundle, load the issue's snippet against the local build,
and confirm the friendly error message prints instead of the
TypeError. The CI assertion guards the bundle contents going forward.

## Candidate plan comment

Looked into this one. The root cause is the 2.x build pipeline
tree-shaking the friendly error system out of the published bundle,
so the error reporter is not there to be called. I plan to fix the
bundler configuration to keep the FES module and add a CI check on
the bundle contents so it cannot regress. Should be a small PR; I'll
report back when the build passes.
