# Single Bet Placement — Defect Report (Part A.2)

**Application:** https://qae-assignment-tau.vercel.app
**User context:** `x-user-id: candidate-DqV3ceKkSxoD`
**Date executed:** 2026-10-04

**What was run:** the three highest-priority scenarios from the test plan — TC-01 (happy path),
TC-02 (insufficient balance) and TC-03 (stake boundary & precision) — plus a short exploratory pass
around the bet-placement flow (reset, HTTP methods, malformed payloads, match catalogue, concurrent
submits). API findings were reproduced live via `requests`/`curl`; the UI findings (balance refresh,
double-click) were confirmed by driving the real app in Chrome with Selenium. Evidence is the actual
request/response and UI readings captured during execution.

## Summary

| Bug ID | Title | Severity |
|--------|-------|----------|
| BUG-01 | Negative stake is accepted and credits the account | Critical |
| BUG-02 | Stake above balance is accepted (API); balance goes negative | Critical |
| BUG-03 | Balance in the UI does not refresh after placing a bet | Critical |
| BUG-04 | Place Bet is not disabled — rapid clicks place multiple bets | High |
| BUG-05 | Past matches are listed and can be bet on | High |
| BUG-06 | `reset-balance` response does not match the persisted balance | Medium |
| BUG-07 | `place-bet` returns `currency: "USD"` instead of EUR | Medium |
| BUG-08 | Malformed JSON body returns `500` instead of `400` | Low |
| BUG-09 | `GET /api/place-bet` returns `200 {}` instead of `405` | Low |

---

### BUG-01 — Negative stake is accepted and credits the account

**Severity:** Critical

**Reproduction Steps:**
1. `POST /api/reset-balance`, then `GET /api/balance` → `120 EUR`.
2. `POST /api/place-bet` with `{ "matchId": "premier-league-manutd-chelsea", "selection": "HOME", "stake": -100 }`.
3. `GET /api/balance`.

**Expected vs Actual:**
- *Expected:* request rejected (`422 invalid_stake_min` — stake must be a positive value ≥ €1.00);
  balance unchanged.
- *Actual:* `200 "Bet placed successfully"` with `stake: -100`, `payout: -245.01`; balance **rises**
  from `120` to `220`.

**Business Impact:** A user can top up their own balance to any amount simply by submitting negative
stakes — an unbounded, trivially exploitable financial-fraud vector.

**Evidence:**
```
place-bet → {"message":"Bet placed successfully","stake":-100,"payout":-245.01,"balance":220,"currency":"USD"}
GET /api/balance → {"balance":220,"currency":"EUR"}
```

---

### BUG-02 — Stake above balance is accepted (API); balance goes negative

**Severity:** Critical

**Reproduction Steps:**
1. `POST /api/reset-balance`; place a `100` stake bet to deplete → `GET /api/balance` = `20`.
2. `POST /api/place-bet` with `{ "matchId": "premier-league-manutd-chelsea", "selection": "HOME", "stake": 50 }`
   (50 > remaining 20, but within the €1–€100 limits).
3. `GET /api/balance`.

**Expected vs Actual:**
- *Expected:* `422 insufficient_balance`; balance unchanged at `20`.
- *Actual:* `200 "Bet placed successfully"`; balance becomes **−30**.

**Business Impact:** Users can place bets with money they do not have, leaving the account in debt.
The documented `insufficient_balance` guard never fires — a direct financial-integrity failure.

**Evidence:**
```
place-bet → {"message":"Bet placed successfully","stake":50,"payout":122.5,"balance":-30,"currency":"USD"}
GET /api/balance → {"balance":-30,"currency":"EUR"}
```

**Note:** This does not happen through the UI. When the user's balance is less than the stake, the
UI blocks the bet and shows an error message. The defect is API-only.

---

### BUG-03 — Balance in the UI does not refresh after placing a bet

**Severity:** Critical

**Reproduction Steps:**
1. Open the app at `?user-id=candidate-DqV3ceKkSxoD` — the header shows `Balance: €120.00`.
2. Select an odds button (e.g. `1` = HOME), enter stake `10`, click **Place Bet**.
3. When the success receipt appears, read the header balance; close the receipt and read it again.
4. Reload the page and read the header balance.

**Expected vs Actual:**
- *Expected:* after a successful bet the displayed balance updates immediately to `€110.00`
  (stake deducted), with no page reload.
- *Actual:* the header balance stays at `€120.00` after placing and after closing the receipt, even
  though the backend already deducted the stake (`GET /api/balance` = `110`). It only corrects to
  `€110.00` after a full page refresh.

**Business Impact:** The user is shown a stale, higher balance and keeps betting against money that
is already gone. Because the UI's own insufficient-balance check reads this stale figure, combined
with the missing server-side guard (BUG-02) a user can unknowingly drive their real balance negative
— a serious trust and financial-clarity failure.

**Evidence**
```
balance_not_refreshed.png
negative_balance.png
```

---

### BUG-04 — Place Bet is not disabled — rapid clicks place multiple bets

**Severity:** High

**Reproduction Steps:**
1. Open the app, select an odds button and enter a stake (e.g. `€1`).
2. Click **Place Bet** several times in quick succession (a fast double/triple-click).
3. Watch the Network tab and the balance.

**Expected vs Actual:**
- *Expected:* the first click disables the button / enters the `Placing...` state, so exactly **one**
  bet is placed and the stake is deducted once.
- *Actual:* the button stays clickable and every click fires a `POST /api/place-bet`. Several succeed
  (`200`) while others hit the concurrency lock (`409`), so **multiple bets are placed for a single
  intended action**. The `409` lock only blocks truly simultaneous overlaps, not rapid sequential
  clicks, so it is not sufficient protection.

**Business Impact:** A user who double-clicks (very common) unintentionally places and pays for
several bets at once — direct, repeated money loss and a likely source of disputes/chargebacks.

**Evidence:**
- Screenshot `docs/double_clicking_place_bet.png` — the Network panel shows several `place-bet`
  responses with `200` interleaved with `409`s from a single click burst.

---

### BUG-05 — Past matches are listed and can be bet on

**Severity:** High

**Reproduction Steps:**
1. `GET /api/matches` and compare each `kickoffDate` against today (`2026-10-04`).
2. `POST /api/place-bet` on a clearly past match, e.g. `premier-league-manutd-chelsea`
   (`kickoffDate: 2026-02-27`).

**Expected vs Actual:**
- *Expected:* only upcoming / pre-match events are listed and bettable (per scope and spec).
- *Actual:* **81 of 103** matches have a `kickoffDate` in the past (earliest `2026-02-27`), and a bet
  on the February match is accepted with `"Bet placed successfully"`. The UI even tags them `PAST`
  yet still shows them.

**Business Impact:** Users can bet on matches that have already been played (outcome known) — a
fairness and integrity exploit, and a breach of the "upcoming only" scope.

**Evidence:**
```
GET /api/matches → 103 matches, 81 with kickoffDate < 2026-10-04 (earliest 2026-02-27)
place-bet on 2026-02-27 match → "Bet placed successfully"
```

---

### BUG-06 — `reset-balance` response does not match the persisted balance

**Severity:** Low

**Reproduction Steps:**
1. `POST /api/reset-balance`.
2. `GET /api/balance` immediately after (reproduced consistently).

**Expected vs Actual:**
- *Expected:* the persisted balance equals the value returned by reset (spec: "Response body and
  persisted state must be consistent after reset").
- *Actual:* reset returns `balance: 125.5`, but `GET /api/balance` returns `120` — off by `5.5`.

**Business Impact:** as this endpoint probably is for testing purposes, I set it as Low.

**Evidence:**
```
POST /api/reset-balance → {"message":"Balance reset successfully","balance":125.5,"currency":"EUR"}
GET  /api/balance       → {"balance":120,"currency":"EUR"}
```

---

### BUG-07 — `place-bet` returns `currency: "USD"` instead of EUR

**Severity:** Low

**Reproduction Steps:**
1. `POST /api/reset-balance`.
2. `POST /api/place-bet` with a valid bet and read `currency` in the response.
3. Compare against `GET /api/balance`.

**Expected vs Actual:**
- *Expected:* `currency: "EUR"` everywhere (spec mandates EUR).
- *Actual:* `place-bet` returns `currency: "USD"`, while `balance` and `reset-balance` return `EUR`.

**Business Impact:** I set it as Low as the balance reduces exactly like it would be in Euros,
not doing any conversion, so it's just a API - contract issue.

**Evidence:**
```
place-bet → "currency":"USD"
GET /api/balance → "currency":"EUR"
```
