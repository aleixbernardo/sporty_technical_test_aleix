# Single Bet Placement — Test Plan (Part A.1)

**Scope:** Desktop web, Soccer/Football, pre-match, single bet only.

**Approach:** Risk-based prioritization. The 9 scenarios below span the core happy path, stake
boundary conditions, financial-integrity negatives, sequential placement, selection validation,
the date/odds filters and filter persistence — the areas where a betting flow carries the most
user, money, and trust risk. They are ordered by priority (Critical → High → Medium).

Where the spec requires validation at the **UI + API** layer, each scenario is checked at **both**:
the UI guard is not assumed to be the only line of security, so the API is called directly —
including with inputs the UI prevents (e.g. extra decimals, submitting without a selection) — to
confirm the server rejects what the web blocks.

> Reference values: stake limits €1.00–€100.00 (2 decimals), odds 1.01–1000.00, currency EUR.

| ID | Title | Priority |
|----|-------|----------|
| TC-01 | Place a valid single bet — end-to-end happy path | Critical |
| TC-02 | Insufficient balance must be rejected | Critical |
| TC-03 | Stake boundary & precision validation | High |
| TC-04 | Place multiple sequential bets (different & same match) | High |
| TC-05 | Double-click Place Bet must not place two bets | High |
| TC-06 | Selection required / invalid selection rejected | Medium |
| TC-07 | Odds filter range validation (out-of-range odds) | Medium |
| TC-08 | Date filter (single day & inclusive range) | Medium |
| TC-09 | Filter persists after placing a bet | Medium |

---

### TC-01 — Place a valid single bet (end-to-end happy path)

**Priority:** Critical

**Risk Rationale:** This is the main test case end-to-end of the product. If this fails,
the user does not bet, which can lead to a lost costumer due to dissatisfaction and
the company does not get revenue.

**Steps:**
1. Reset balance for the user
2. Open app with `?user-id=<id>`.
3. On an upcoming match, select one odds button (e.g. `1` = HOME).
4. In the bet slip, enter a valid stake, e.g. `10.00`.
5. Confirm the slip shows stake, available balance, and potential payout = `stake × odds`.
6. Click **Place Bet**.

**API check (same flow, direct):**
- `POST /api/place-bet` with `{ matchId, selection, stake: 10 }` → `200` returning `message`,
  `matchId`, `selection`, `stake`, `odds`, `payout` (= stake × odds), `balance` and `currency`.
- `GET /api/balance` afterwards reflects the same deducted balance (persisted state matches the
  response).

**Expected Result:**
- Button shows loading state (`Placing...`), then resolves to success.
- Success receipt modal shows: Bet ID, match details, selection, stake (10.00), odds at
  placement, potential payout (= 10.00 × odds), and placement timestamp.
- Balance decreases by exactly the stake, not needing a refresh.
- Closing the receipt returns to the main flow with **no active selection**.

---

### TC-02 — Insufficient balance must be rejected

**Priority:** Critical

**Risk Rationale:** Allowing a stake above the available balance is a direct financial-integrity
failure (betting money that doesn't exist, balance going negative).

**UI steps:**
1. Reset balance, then deplete it below €100 (e.g. place a €100 bet so only a small balance remains).
2. With balance below the intended stake, select an outcome and enter a stake greater than the
   remaining balance but still within €1–€100 (e.g. stake €50 with €20 left).
3. Attempt to place the bet.

**API steps (with endpoints):**
1. `POST /api/reset-balance` — start from a known balance.
2. `GET /api/balance` — read the current balance (`B`).
3. `POST /api/place-bet` with `{ matchId, selection: "HOME", stake: 100 }` — deplete so only a
   small balance remains.
4. `GET /api/balance` — confirm the remaining balance is low (e.g. `~20`).
5. `POST /api/place-bet` with `{ matchId, selection: "HOME", stake: 50 }` — a stake greater than
   the remaining balance but still within €1–€100.
6. `GET /api/balance` — confirm the balance did not change after the rejected bet.

**Expected Result:**
- UI shows **"Insufficient balance"**; Place Bet is blocked/rejected.
- Step 5 → API returns `422` with `error: insufficient_balance`.
- Step 6 → balance is **unchanged** vs step 4 (no partial deduction).

---

### TC-03 — Stake boundary & precision validation

**Priority:** High

**Risk Rationale:** Boundary off-by-one errors are the most common validation failure and here
they directly govern how much money is accepted per bet. Must verify both UI feedback and API
rejection at the exact edges, on negative values and on invalid precision.

**UI steps (data-driven, each value a sub-case):**
1. Reset balance for the user
2. Open app with `?user-id=<id>`.
3. On an upcoming match, select one odds button (e.g. `1` = HOME).
4. Enter and attempt to place each stake:
   - `1.00` (lower bound) · `100.00` (upper bound) — **accept**
   - `0.99` (just below min) · `100.01` (just above max) — **reject**
   - `-5` (negative) — **reject** (stake must be positive)
   - `5.123` (3 decimals) — **reject or cut** (precision)
   - `abc` / empty — **reject / Place Bet blocked** (non-numeric / required)

**API steps (with endpoint):** send `POST /api/place-bet` with a valid `matchId` + `selection` and
each stake value below — including the ones the UI prevents you from even typing. The spec requires
validation at the **UI + API** layer, so whatever the web blocks must also be rejected server-side.
- `stake: 1.00` → expect `200`
- `stake: 100.00` → expect `200`
- `stake: 0.99` → expect `422`
- `stake: 100.01` → expect `422`
- `stake: -5` → expect `422`
- `stake: 5.123` → expect `422`
- `stake: "abc"` → expect `422`
- `stake` missing → expect `422`

**Expected Result:**
- *UI:* `1.00` and `100.00` place successfully. `0.99` → "Minimum stake is €1.00"; `100.01` →
  "Maximum stake is €100.00". The web app clamps input to 2 decimals so `5.123` can't be entered,
  a negative stake is blocked (no `-` / Place Bet disabled), and non-numeric/empty blocks Place Bet.
- *API:* `1.00`/`100.00` → `200`. Everything the UI blocks is also rejected with `422` —
  `0.99` and `-5` → `invalid_stake_min`, `100.01` → `invalid_stake_max`,
  `5.123` → `invalid_stake_precision`, `abc` or missing stake → `invalid_stake_type`.

---

### TC-04 — Place multiple sequential bets (different & same match)

**Priority:** High

**Risk Rationale:** A real user rarely stops at one bet. "Single bet only" means one selection per
placement, not one bet per session, so placing a bet must not block the next one. This checks that
each bet is independent (its own receipt and Bet ID), the slip resets between bets, and the balance
deducts cumulatively and correctly. The spec defines no per-match uniqueness rule, so betting the
**same** match again (even a different outcome) is allowed.

**Steps:**
1. Reset balance.
2. Place bet #1 on match A (e.g. Man Utd–Chelsea, HOME, stake `10`). Close the receipt.
3. Place bet #2 on a **different** match B (e.g. Real–Barça, AWAY, stake `20`). Close the receipt.
4. Place bet #3 on the **same** match A again, same selection (HOME stake `5`).

**API check (same flow, direct):** three separate `POST /api/place-bet` calls, then `GET /api/balance`.

**Expected Result:**
- All three placements succeed, each with its own receipt and distinct Bet ID.
- Between bets the slip is empty (no leftover selection).
- Balance decreases cumulatively by the sum of the stakes (`10 + 20 + 5 = 35` total).
- API returns three `200`s and `GET /api/balance` reflects the cumulative total; the same match
  can be bet more than once.

---

### TC-05 — Double-click Place Bet must not place two bets

**Priority:** High

**Risk Rationale:** A fast double-click (or a laggy response) could submit the same bet twice and
deduct the stake twice — a direct money risk and a classic double-submit scenario. The button must
go into its `Placing...` state and disable on the first click so the second does nothing; the
server's per-user concurrency lock is the backstop.

**Steps:**
1. Reset balance. Select an outcome and enter a valid stake (e.g. `10`).
2. Double-click **Place Bet** as fast as possible, before the button disables.
3. Check the receipt(s) and the resulting balance.

**Expected Result:**
- Only **one** bet is placed: a single receipt with a single Bet ID.
- Balance is deducted exactly once (by a single stake), not twice.
- The button disables / shows `Placing...` on the first click, so the second click is a no-op.
- Server backstop: if two requests do race through, the API rejects the duplicate with
  `409 bet already in progress` (reproducible with a burst of concurrent place-bets).

---

### TC-06 — Selection required / invalid selection rejected

**Priority:** Medium

**Risk Rationale:** A bet with no/invalid outcome is meaningless and must be blocked at the UI
and rejected by the API enum. Also guards the "new selection replaces previous" rule, preventing
ambiguous multi-selection state.

**UI steps:**
1. Open app, enter a valid stake **without** selecting any odds → observe Place Bet.
2. Select `1` (HOME), then click `X` (DRAW) on the same match → observe the slip.

**API steps (bypassing the UI):** the UI won't let you submit without a selection, so hit the API
directly to confirm the server enforces it too:
- `POST /api/place-bet` with `selection: "WIN"` (invalid value).
- `POST /api/place-bet` with the `selection` field **missing**.
- `POST /api/place-bet` with the `matchId` field **missing**, and with an **unknown** `matchId`.

**Expected Result:**
- *UI:* with no selection, Place Bet is disabled/blocked. Selecting a new outcome **replaces** the
  previous one (single active selection).
- *API:*
  - invalid or missing `selection` → `422 invalid_selection`
    ("Selection must be one of: HOME, DRAW, AWAY.").
  - missing `matchId` → `422 invalid_match_id`; unknown `matchId` → `422 invalid_match`.

---

### TC-07 — Odds filter range validation (out-of-range odds)

**Priority:** Medium

**Risk Rationale:** Invalid filtering on UI/UX can lead to a bad user experience and 
therefore dissatisfaction of the user, as well as not finding the game that the user
wants to bet in and possibly a missing bet which is less revenue for the company.

**UI steps:**
1. Open app (default `Odds: 1.00 - 10.00` → all matches shown).
2. Apply a valid inclusive range (e.g. min `2.00`, max `3.00`).
3. Apply an **invalid** range where min > max (e.g. min `5.00`, max `2.00`).
4. Apply and **invalid**  range where odds is < 1
5. Click reset button and check if filter resetting works.

**API steps (with endpoint):** the filter is client-side, so no tests here.

**Expected Result:**
- *UI:* a valid range shows only matches whose any of the 3 odds fall inside it (inclusive of both bounds). An
  invalid range (min > max) is **rejected with clear feedback** (not silently empty), as required
  by spec 2.6.

---

### TC-08 — Date filter (single day & inclusive range)

**Priority:** Medium

**Risk Rationale:** Invalid filtering on UI/UX can lead to a bad user experience and 
therefore dissatisfaction of the user, as well as not finding the game that the user
wants to bet in and possibly a missing bet which is less revenue for the company.

**UI steps:**
1. Open app (default is `Date: All` → all `103` matches shown).
2. Filter by a **single day** that has matches (e.g. `2026-03-01`).
3. Filter by a **date range** (e.g. `2026-03-01` → `2026-03-05`), checking the boundary dates
   themselves are included.
4. Filter by a day (e.g. `2026-04-01`) and then click a day before it (`2026-03-01`)
5. Reset filter and check 103 matches shown

**Expected Result:**
- *UI:* `Date: All` shows every match. A single-day filter shows only that day's matches. A range
  shows only matches within `[start, end]` **inclusive** of both bounds. When reverting the filters as in *4* , filter works correctly.

---

### TC-09 — Filter persists after placing a bet

**Priority:** Medium

**Risk Rationale:** A user who filters the list, picks a match and bets expects to return to the
**same filtered view** to keep betting. If placing a bet silently resets the filter back to "All",
the user loses their context and has to re-filter every time — a frustrating UX that discourages
further bets (less revenue).

**UI steps:**
1. Apply a filter (e.g. `Odds: 2.00 - 3.00`, or a date range) so the list is narrowed.
2. Select a match **from the filtered results** and place a valid bet.
3. Close the success receipt and look at the match list and the filter controls.

**Expected Result:**
- The filter is **still applied** after the bet: the same filtered results are shown and the filter
  control still displays the chosen range/date (it is not reset to `All`).
- Only the bet slip is cleared (no active selection); the filter state is preserved.
