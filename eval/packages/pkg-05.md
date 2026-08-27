# Eval package: pkg-05

- source: conda/conda#16502
- captured: 2026-08-18
- calibration: false

## Repo facts (captured 2026-08-18)

- repo: conda/conda (7485 stars, archived: no)
- description: A system-level, binary package and environment manager running on all major operating systems and platforms.
- latest release: 26.7.0 (2026-07-31)
- bug reports: template asks for a descriptive title, a duplicate search, what happened, and the output of `conda info` and `conda list`
- contribution policy (CONTRIBUTING.md, section "Generative AI"): generative AI tools welcome; you are responsible for all contributions and must review and understand AI-generated content before including it in a pull request

## Issue

### Cached notices block newer notices (#16502)

opened by danyeaw (MEMBER) on 2026-08-06, state open, labels: type::bug, source::anaconda

Per-channel notice responses are cached (`cached_response` in
`conda/notices/cache.py`) and considered fresh until any cached
notice's expiry passes (or is missing). While fresh, no network
request is made, so a notice published later for that channel is
invisible until the earliest cached expiry elapses.

Concrete scenario:

1. Channel publishes notice A with `expires_at` 90 days out; a user's
   client fetches and caches it.
2. One week later the channel publishes notice B (in addition to A).
3. The user's client serves the cached payload for about 83 more
   days; notice B is never shown during that window.

Expected: staleness is bounded so newly published notices reach users
within a reasonable interval.

Actual: staleness is unbounded and controlled entirely by the
previously published notices' expiry dates, which the channel owner
may legitimately set far in the future.

Suggested fix in the issue: add a maximum age to the per-channel
response cache, recommend using the `NOTICES_DECORATOR_DISPLAY_INTERVAL`
constant (24h).

## Thread highlights (2 comments total)

- 2026-08-12 travishathaway (CONTRIBUTOR): the right variable to use is the `NOTICES_DECORATOR_DISPLAY_INTERVAL` constant, currently 24 hours, which would prevent the described behavior
- 2026-08-17 danyeaw (MEMBER): agrees, and clarifies that the TTL still needs to be wired into `get_notice_response_from_cache()` to fix the issue

## Repro evidence

The reproduction this plan builds on, excerpted from the accepted
repro report:

Environment: conda 26.7.0 (Miniconda), Python 3.13, Ubuntu 24.04; a
local file-based test channel.

Steps:

1. Served a `notices.json` on the test channel containing notice A
   with `expires_at` 90 days out.
2. `conda notices -c <test-channel>`: notice A prints; the response
   lands in the notices cache directory.
3. Added notice B to the channel's `notices.json` (A unchanged).
4. `conda notices -c <test-channel>` again (minutes later): only
   notice A prints. No request hits the channel server (verified in
   the file server's access log: one request total).
5. Control: deleted the cache file and re-ran: A and B both print,
   and the access log shows a second request.

Expected: notice B reaches the client within a bounded interval.

Actual: the cached response for the channel is treated as fresh until
notice A's expiry, so B is invisible; only clearing the cache (or
waiting out the 90 days) surfaces it, matching the issue.

## Candidate plan

Diagnosis: as the issue states and the repro confirms, cache freshness
in `conda/notices/cache.py` is derived only from the cached notices'
own `expires_at` values, so one long-lived notice pins the whole
channel response.

Scope, one bounded change: add a maximum cache age to the freshness
check in `get_notice_response_from_cache()`, using the existing
`NOTICES_DECORATOR_DISPLAY_INTERVAL` constant (24h) as the cap, per
the direction already settled in the thread. Not in scope: the notice
display cadence itself, channel protocol changes, or cache storage
format.

Files: `conda/notices/cache.py` (the freshness check),
`tests/notices/test_cache.py` (new cases).

Approach: compute the cached response's age from the cache file's
stored timestamp; treat the response as stale when age exceeds the
constant, even if every cached notice is unexpired. Add unit tests
for: unexpired notices but stale-by-age (refetch), fresh-by-age (no
refetch), and the existing expiry-based path unchanged.

Test plan: re-run the repro scenario with the cache file's timestamp
backdated by 25 hours: step 4 must fetch and print A and B (access
log shows the second request). Un-backdated, step 4 must stay served
from cache. Unit tests as above.

Risk: none identified beyond one extra network request per channel
per 24h, which is the constant's existing meaning.

## Candidate plan comment

I reproduced the pinning behavior with a local test channel (report
above) and would like to implement the fix along the lines already
agreed here: wiring `NOTICES_DECORATOR_DISPLAY_INTERVAL` into
`get_notice_response_from_cache()` as a maximum response age, with
unit tests for the stale-by-age and fresh-by-age paths. Nothing
outside the cache freshness check. I'll report back with the PR once
the tests pass locally.
