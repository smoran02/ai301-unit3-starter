# Eval package: pkg-06

- source: kubernetes/minikube#21408
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: kubernetes/minikube (32040 stars, archived: no)
- description: Run Kubernetes locally.
- latest release: v1.38.1 (2026-02-19)
- bug reports: template asks what happened, the exact command to reproduce, the full output of the failed command, the output of `minikube logs`, the operating system, and the driver
- contribution policy (CONTRIBUTING.md): standard Kubernetes-project contribution guide (CLA, DCO); no stated AI policy

## Issue

### containerd: preloaded images fail to save (#21408)

opened by nirs (MEMBER) on 2025-08-23, state open, labels: kind/bug, lifecycle/frozen

Saving preloaded images (e.g. `registry.k8s.io/pause:3.10`) with the
containerd runtime is broken, creating an empty tar. Saving images
pulled into minikube works. The reporter suspects the preloaded
images were not prepared with containerd and their internal structure
differs from images pulled into the cluster by containerd.

Repro (macOS/vfkit shown; Linux/kvm behaves the same):

```
% minikube start --driver vfkit --container-runtime containerd
% minikube image save registry.k8s.io/pause:3.10 test.tar; echo $?
0
% file test.tar
test.tar: empty
```

## Thread highlights (10 comments total)

- 2025-08-23 nirs (MEMBER): running with `--alsologtostderr --v=10` reveals interesting failures that are not reported to the user
- 2025-08-23 nirs (MEMBER): notes minikube bundles containerd 1.7.23 while 1.7.28 is current

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: minikube v1.38.1 (Homebrew), vfkit driver, containerd
runtime (bundled 1.7.23), macOS 15.6 (arm64).

Steps:

1. `minikube start --driver vfkit --container-runtime containerd`
2. `minikube image save registry.k8s.io/pause:3.10 test.tar; echo $?`
   prints `0`
3. `file test.tar` prints `test.tar: empty`
4. Verbose re-run (`--alsologtostderr --v=10`) shows an export error
   from the containerd runtime for the preloaded image; the command
   still exits 0 with the empty tar.

Control run: `minikube image pull nginx:alpine` followed by
`minikube image save nginx:alpine nginx.tar` produces a valid tar
(`file` reports a POSIX tar archive; `tar tf` lists layers).

Expected: saving a preloaded image produces a valid tar, or the
command fails loudly.

Actual: empty tar with exit 0 for preloaded images only, matching the
issue; the underlying export error is swallowed.

## Candidate plan

### Problem statement

The preload/save pipeline for containerd is structurally unsound, and
this issue is the visible tip. Fixing only the save path would leave
the deeper mismatch in place, so this plan addresses the pipeline as
a whole.

### Proposed changes

1. Regenerate the preload tarballs so their internal layout is
   produced by containerd itself (native content store layout),
   replacing the current generation path in the preload build
   scripts.
2. Upgrade the bundled containerd from 1.7.23 to 1.7.28 for every
   runtime and driver combination, since we are on an old patch
   series anyway.
3. Introduce a unified image-operations abstraction so `image save`,
   `image load`, and `image ls` share one code path across docker,
   containerd, and cri-o instead of three divergent ones.
4. Surface export errors to the user (non-zero exit) instead of
   swallowing them.
5. Add a CI matrix job exercising image save/load for each runtime so
   this class of drift cannot land again.

### Files and areas

Preload generation scripts, `pkg/minikube/cruntime/` (all three
runtime implementations), the image command layer in
`cmd/minikube/cmd/image.go`, CI workflow definitions.

### Test plan

After the pipeline rework, `minikube image save` for a preloaded
image produces a valid tar on containerd (the repro's step 2 and 3
with `file` showing a POSIX tar), and the new CI matrix passes for
all three runtimes.

## Candidate plan comment

I reproduced the empty-tar save on vfkit/containerd (report above)
and traced it to the preload structure mismatch the issue suspects.
Rather than patch just the save path, I plan to fix the pipeline
properly: regenerate preloads in containerd's native layout, bump the
bundled containerd to 1.7.28 across runtimes, unify the image
save/load code paths behind one abstraction, make export errors fail
loudly, and add a runtime CI matrix for image operations. It is a
bigger change than the one-line symptom fix, but it removes the whole
class. I'll start with the preload generation piece.
