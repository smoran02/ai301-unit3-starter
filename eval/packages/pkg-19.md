# Eval package: pkg-19

- source: vuejs/core#9396
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: vuejs/core (54212 stars, archived: no)
- description: Vue.js is a progressive, incrementally-adoptable JavaScript framework for building UI on the web.
- latest release: v3.5.41 (2026-08-05)
- bug reports: template requires the version, a minimal reproduction link (SFC playground or repo), steps to reproduce, what is expected, and what is actually happening
- contribution policy (.github/contributing.md): standard contribution guide; no stated AI policy

## Issue

### Transition: custom appear(-active/to) classes stay on the element after transition ends. (#9396)

opened by cess123456 (NONE) on 2023-10-13, state open, labels: bug, scope: transition, p3-minor-bug

Vue 3.2.20, with an SFC playground reproduction linked. When using
the Transition component with `appear` and a custom `appearToClass`,
wrapping a component that uses `v-show` (initially false), the class
added via `appearToClass` never disappears from the node after the
transition ends.

Expected: the custom appear-to class is removed when the transition
finishes, like the built-in classes.

Actual: the `appearToClass` value remains on the element
indefinitely (screenshot in thread shows the class still present).

## Thread highlights (3 comments total)

- 2023-10-13 LinusBorg (MEMBER): these classes are not meant to stay on the element; they are added for one frame at the end and removed right after the transition finishes, so this works as intended
- 2023-10-16 cess123456 (NONE): agrees they should not stay, but they do, with a screenshot showing the class still on the node; that is the bug

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: Vue 3.5.41, Vite playground, Chromium 138, macOS 14.5.

Steps:

1. Minimal SFC: `<Transition appear appear-to-class="fade-appear-to">`
   wrapping a `<p v-show="shown">` that starts false and is set true
   in `onMounted`.
2. After the appear transition completes (transition duration 300ms,
   checked at t+2s), inspected the element in devtools.

Artifact: the element's classList at t+2s reads
`["fade-appear-to"]`; an `animationend`/`transitionend` listener
confirms the transition fired and ended.

Control: the same component with the default classes (no
`appear-to-class` prop): at t+2s the classList is empty; the
built-in `v-enter-to` class was removed at transition end as
documented.

Expected: the custom appear-to class is removed at transition end
exactly like the default class in the control.

Actual: only the custom-named class leaks and stays on the element,
matching the issue's screenshot on current 3.5.41.

## Candidate plan

### Background

Transition's class bookkeeping has grown organically across enter,
leave, and appear variants, with custom-class props layered on. This
leak shows the bookkeeping needs a real owner, so this plan
modernizes the whole lifecycle rather than patching one removal.

### Proposed changes

1. Rebuild the Transition class lifecycle as an explicit state
   machine module (`runtime-dom/src/components/TransitionState.ts`)
   that owns every add/remove for enter, leave, and appear phases,
   replacing the scattered `addTransitionClass` /
   `removeTransitionClass` calls.
2. Unify appear handling with enter handling so custom appear-*
   classes flow through the same removal path as the defaults (the
   leak's class of bug becomes unrepresentable).
3. Add a `persistClass` prop for users who deliberately want a class
   retained after the transition, since the state machine makes that
   cheap to offer.
4. Migrate the runtime-dom Transition tests to a new table-driven
   harness that asserts the full class timeline per phase, replacing
   the current ad hoc assertions.
5. Deprecate the internal hooks the old code exposed to
   TransitionGroup and port TransitionGroup onto the state machine.

### Test plan

The repro's custom appear-to class is removed at transition end, and
the migrated Transition and TransitionGroup suites pass on the new
harness.

## Candidate plan comment

Reproduced on 3.5.41 (report above; the control shows only
custom-named classes leak). Rather than chase the one missing
removal, I plan to rebuild Transition's class lifecycle as a state
machine, unify appear with enter, port TransitionGroup onto it, add a
`persistClass` opt-in, and migrate the tests to a timeline harness.
That makes this whole class of leak unrepresentable. It touches most
of the transition code, so I'd open it as an RFC-style draft PR
first.
