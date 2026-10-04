"""API test — the end-to-end "place a bet" business flow, via the API directly.

Why this test: it validates the core money path of the product at the contract level —
fetch the catalogue, place a bet on a real match, and confirm the server computes the
payout and debits the balance correctly. It mirrors what the UI does but without a
browser, so it is a fast, stable guard for the most business-critical behaviour.

Note: the starting balance is read from `GET /api/balance` rather than from the
reset-balance response, because those two values are not consistent here (BUG-06).
"""

import allure
import pytest

from schemas.balance import Balance
from schemas.place_bet import PlaceBetResponse
from utils.api.api_balance import get_balance
from utils.api.api_place_bet import place_bet
from utils.common.common_variables import HttpStatus, Selection

STAKE = 10


@allure.epic("Single Bet Placement")
@allure.feature("Place bet (API)")
@allure.story("Happy path")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Placing a bet debits the balance and returns the correct payout")
@allure.description(
    "Fetches the match catalogue, places a HOME bet on the first match and verifies "
    "the API contract: payout = stake x odds and the balance is debited by the stake, "
    "cross-checked against GET /api/balance. Responses validated with pydantic schemas."
)
@allure.testcase("tc-01", "TC-01: Place a valid single bet (happy path)")
@pytest.mark.api
def test_place_bet_debits_balance_and_returns_payout(first_match, fresh_balance):
    with allure.step("Read the starting balance from GET /api/balance"):
        start = Balance(**get_balance().json())
        allure.attach(str(start.balance), "start_balance", allure.attachment_type.TEXT)

    with allure.step(f"Place a HOME bet of {STAKE} on '{first_match.id}'"):
        response = place_bet(first_match.id, Selection.HOME, STAKE)
        assert response.status_code == HttpStatus.OK, response.text
        allure.attach(response.text, "place-bet response", allure.attachment_type.JSON)

    with allure.step("Validate the place-bet response contract (schema + values)"):
        bet = PlaceBetResponse(**response.json())
        assert bet.match_id == first_match.id
        assert bet.selection == Selection.HOME
        assert bet.stake == STAKE
        assert bet.odds == first_match.odds.home
        assert bet.payout == pytest.approx(STAKE * first_match.odds.home)
        assert bet.balance == pytest.approx(start.balance - STAKE)

    with allure.step("Confirm the persisted balance reflects the deduction"):
        after = Balance(**get_balance().json())
        assert after.balance == pytest.approx(start.balance - STAKE)
