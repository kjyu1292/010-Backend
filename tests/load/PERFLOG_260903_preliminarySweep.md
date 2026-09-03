# PERF_LOG_2026-09-03_preliminary-sweep.md

Load test results for the auth + players endpoints. Covers the initial
preliminary sweep and the follow-up isolation run used to confirm the
event-loop-blocking hypothesis. 

## All runs — metric comparison

| Metric | Run 1 (2026-09-03, combined) | Run 2 (2026-09-03, combined, post-fix) | Run 3 (2026-09-03, isolated) | Run 4 (2026-09-03, combined, post-async-fix) |
|---|---|---|---|---|
| Script | `preliminary_sweep.js` | `preliminary_sweep.js` | `players_isolated.js` | `preliminary_sweep.js` |
| Scope | register+login+auth_me+players GET/PATCH, chained per iteration | same | players GET+PATCH only, tokens pre-created in `setup()` | same as Run 1/2 |
| register_duration p95 | 5.21s | 7.21s | N/A (not in scope) | 4.98s |
| login_duration p95 | 4.6s | 5.48s | N/A (not in scope) | 2.12s |
| auth_me_duration p95 | 2.94s | 2.53s | N/A (not in scope) | **221.96ms** |
| players_get_duration p95 | 827ms | 2.91s | 9.92ms | **200.67ms** |
| players_patch_duration p95 | 669ms | 760ms | 21.43ms | **113.79ms ✓ PASS** |
| error rate | 40.00% | 0.00% | 0.00% | 0.00% |
| http_reqs total | 2,280 | 1,935 | 6,250 | 3,995 |
| throughput (req/s) | 10.86 | 9.20 | 27.99 | **18.88** |
| max VUs | 25 | 25 | 25 | 25 |

## Run 1 — Preliminary sweep, initial

**What changed vs. previous run**: first run, no baseline to compare against.

**Next step**: 40% error rate needs explaining before latency can be trusted. Two live suspects: the `/auth/register` rate limiter throttling k6's own traffic (single source IP), and a stale Docker image missing the newly-added `players` router entirely.

## Run 2 — Preliminary sweep, after disabling rate limiter + rebuilding container

**What changed vs. previous run**: rate limiter on `/auth/register` disabled; Docker image rebuilt (Run 1's `players/me` 404s traced to the running container predating the `players` router — a stale build, not a load effect).

**Next step**: errors resolved (40% → 0%), but latency got *worse*, not better, and `players_get` — a cheap DB read with no bcrypt involvement — degraded the most (827ms → 2.91s p95). This pointed away from per-endpoint causes and toward something shared across all endpoints (event loop blocking from synchronous bcrypt calls in register/login). Needed an isolated run to confirm before touching any code.

## Run 3 — Isolated players/me sweep (register/login moved to `setup()`, outside the measured window)

**What changed vs. previous run**: register+login removed from the measured load entirely — 30 tokens pre-created once in `setup()`, the ramping-VU stages only ever call `players/me` GET/PATCH.

**Result**: p95 dropped from 2.91s → 9.92ms (GET) and 760ms → 21.43ms (PATCH) — roughly 35x and 35x improvement respectively, with 0% errors and nearly 3x the throughput of the combined runs. This confirms `players/me` was never actually slow on its own; **register/login's synchronous bcrypt calls were blocking the single-process event loop and starving unrelated concurrent requests**, exactly as hypothesized after Run 2.

**Next step**: apply the fix now that it's confirmed rather than assumed —
1. Wrap `get_password_hash`/`verify_password` in `asyncio.to_thread` in `app/auth/service.py`, so hashing no longer blocks the event loop.
2. Run multiple uvicorn workers (`--workers N`) so register/login can actually use more than one CPU core.
3. Re-run `preliminary_sweep.js` (the combined script) afterward — if the fix worked, `players_get`/`players_patch` p95 in the *combined* run should now approach Run 3's isolated numbers, and `register`/`login` p95 should drop meaningfully too, even though bcrypt's raw cost doesn't disappear.

## Run 4 — Preliminary sweep, after `asyncio.to_thread` + multi-worker uvicorn

**What changed vs. previous run**: `get_password_hash`/`verify_password` wrapped in `asyncio.to_thread`; `main.py` switched to string import (`"app.app:app"`) with `workers=4` so uvicorn actually spawns multiple processes.

**Result**: cross-contamination fix confirmed working at combined-load scale, not just in isolation —
- `players_patch_duration` p95: 760ms → **113.79ms, now passes its threshold**
- `players_get_duration` p95: 2.91s → 200.67ms (just barely over the 200ms threshold, essentially resolved)
- `auth_me_duration` p95: 2.53s → 221.96ms (same story — near-threshold, night-and-day vs. Run 2)
- Throughput roughly doubled (9.2 → 18.88 req/s), total completed iterations roughly doubled (387 → 799) in the same 3m30s window

This confirms the diagnosis from Run 3 was correct and generalizes under real combined load, not just the artificial isolated case.

**What's still failing**: `register` (4.98s p95) and `login` (2.12s p95) remain over threshold, though both improved from Run 2 (7.21s → 4.98s register, 5.48s → 2.12s login). These two are the only endpoints that still directly call bcrypt themselves — `asyncio.to_thread` stopped them from blocking *other* endpoints, but didn't make bcrypt itself faster; each individual hash still costs what it costs, and now that cost is genuinely CPU-bound work competing across however many real cores the host/container actually has.

**Next step**:
1. Confirm `nproc` (or the container's CPU allocation, if `docker-compose.yml` sets a `cpus:` limit) actually provides ≥4 cores — `workers=4` doesn't help if the host only has 1-2 cores to schedule them on.
2. If cores are the limit, this may be close to the realistic ceiling for bcrypt at this VU count on this hardware — worth deciding whether the current register/login thresholds (800ms/500ms) were reasonable targets in the first place, given bcrypt is deliberately expensive by design, or whether they should be revised to something evidence-based instead of guessed.
3. If further improvement is genuinely needed beyond hardware limits, the next lever isn't more async/thread tricks — it's horizontal (more app replicas behind the load balancer) or offloading hashing to a dedicated worker queue, both bigger architectural changes than this round's fix.

---

## Full metric breakdown, all runs

| Run | Endpoint | avg | median | p90 | p95 | max |
|---|---|---|---|---|---|---|
| Run 1 | register | 2.48s | 2.52s | 4.49s | 5.21s | 8.59s |
| Run 1 | login | 1.96s | 1.71s | 3.83s | 4.6s | 7.01s |
| Run 1 | auth/me | 1.1s | 858ms | 2.2s | 2.94s | 7.39s |
| Run 1 | players/me GET | 261ms | 212ms | 645ms | 827ms | 1.25s |
| Run 1 | players/me PATCH | 227ms | 212ms | 628ms | 669ms | 1.19s |
| Run 2 | register | 3.13s | 3.23s | 5.15s | 7.21s | 10.94s |
| Run 2 | login | 2.26s | 1.97s | 4.81s | 5.48s | 9.89s |
| Run 2 | auth/me | 828ms | 494ms | 1.94s | 2.53s | 5.84s |
| Run 2 | players/me GET | 856ms | 497ms | 2.27s | 2.91s | 10.37s |
| Run 2 | players/me PATCH | 236ms | 54ms | 546ms | 760ms | 6.2s |
| Run 3 | players/me GET | 6.06ms | 5.3ms | 8.03ms | 9.92ms | 131.95ms |
| Run 3 | players/me PATCH | 10.09ms | 8ms | 13.52ms | 21.43ms | 129.84ms |
| Run 4 | register | 1.98s | 1.41s | 4.27s | 4.98s | 6.93s |
| Run 4 | login | 758.22ms | 550.15ms | 1.62s | 2.12s | 3.92s |
| Run 4 | auth/me | 74.95ms | 46.82ms | 65.96ms | 221.96ms | 2.53s |
| Run 4 | players/me GET | 83.95ms | 52.88ms | 107.04ms | 200.67ms | 1.78s |
| Run 4 | players/me PATCH | 70.69ms | 52.76ms | 79.07ms | 113.79ms | 1.62s |
