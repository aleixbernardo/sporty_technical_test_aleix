# Strategy & Recommendations (Part C)

## Why these 2 tests were automated

I automated the **single highest-value flow at both layers it lives on**:

- **E2E UI — place a single bet (`tests/ui/test_place_bet_journey.py`).** This is the core revenue
  journey and the one test that exercises the most integration risk in a single run: odds selection
  → stake entry → payout calculation → `Placing...` state → success receipt. If this is green, a
  real user can actually bet. It is the obvious P0 to protect against regressions.
- **API — place-bet happy path (`tests/api/test_place_bet_happy_path.py`).** The same money flow at
  the contract level: it fetches the catalogue, places a bet and verifies `payout = stake × odds`
  and the balance deduction, with responses validated by pydantic schemas. It is fast, deterministic
  and free of browser flakiness, so it pinpoints whether a failure is in the business logic or only
  in the UI.

Together they cross-check each other: UI green + API green means the critical path works end to end
on both the client and the server.

### Why these over other candidates

- I picked the application's most important feature — **betting** — and automated it as smoke tests
  from both the full web end-to-end and the API directly. If either of these two tests fails, the
  build should not go to production, because it carries all the business risk.
- I deliberately kept the corner cases out of this first set: they are many and individually
  low-impact, and several are already **known defects** (see `bug-report.md`) that would only produce
  red tests. They belong in the bug tracker and in a future data-driven layer, not in the smoke set.

## What I intentionally left as manual-only, and why

- **Boundary & validation matrix** (stake min/max/precision/negative/non-numeric, invalid selection,
  missing/unknown matchId). Many permutations, each low-impact; catalogued in `test-plan.md` and
  verified by hand. Better as a future parametrised API suite than as top-level tests.
- **Known defects** (negative stake, insufficient balance, currency, reset mismatch, past matches,
  malformed-JSON 500). Verified manually with evidence; not automated as passing tests because they
  would be red — they become regression tests once fixed.
- **Error modal / recovery (Rebet / Close).** No deterministic trigger from the UI (the `409` is a
  concurrency race, the `500` needs a malformed body the UI never sends), so it stays exploratory
  until there is a reliable hook (e.g. a network stub).
- **Filters (date / odds) and persistence.** Client-side behaviour with product ambiguity (the odds
  filter matches on *any* outcome) — worth confirming intent before locking it into automation.
- **Exploratory / visual / UX.** Human judgement finds the high-impact bugs; not worth brittle
  automation yet.

## Top recommendations if this were to scale

1. **CI/CD + reporting.** Add CI (e.g. GitHub Actions), provisioning Python 3.13 and Chrome. Tag the
   two critical tests with `@pytest.mark.smoke` and split the work across four pipelines:
   - **Smoke** — `pytest -m smoke`. Runs on every push and pull request, **gates merges on green**.
     Fast feedback on the critical path only.
   - **Regression** — `pytest` (the whole suite). Runs on merge to `main` and before releases;
     **parallelised** with `pytest-xdist`, with `pytest-rerunfailures` to absorb UI flakiness and a
     **browser matrix**.
   - **Scheduled (cron)** — the full regression on a nightly `schedule:` trigger, to catch
     environment/data drift even when nobody pushed.
   - **Deploy-triggered** — a pipeline that listens for the deploy workflow via `workflow_run`
     (and is also callable on-demand via `workflow_dispatch`), so each deployment automatically
     runs smoke (then regression) against the freshly deployed environment.

   Every run **publishes the Allure report to the `gh-pages` branch** (served via GitHub Pages, with
   history kept across runs) and **posts the report URL to a Slack/Teams channel**, so the team sees
   the result and the hosted report without opening the pipeline. This is intentionally out of scope
   for the current deliverable but is the first thing I would add to make the suite a real safety net.
2. **Test-data & environment strategy.** Parametrise the tests and the API helpers to run under
   distinct `user-id`s, so each test has an isolated balance and several users' actions can be
   exercised concurrently without shared-state collisions. Add a config layer per environment
   (staging/prod) and factory fixtures for matches/bets — the prerequisite for running the suite in
   parallel safely.
3. **Performance & load testing.** Add a performance layer (e.g. k6 or Locust) that drives
   `place-bet`, `matches` and `balance` under concurrent load, checking latency and correctness under
   contention — in particular the per-user bet lock (the `409` behaviour) and that balances stay
   consistent when many bets land at the same time.
