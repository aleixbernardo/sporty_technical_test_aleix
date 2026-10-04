"""E2E UI test — the critical "place a single bet" journey.

Why this test: placing a bet is the core revenue path of the product. If a user cannot
select an outcome, enter a stake and receive a confirmed receipt, nothing else matters.
This exercises the full happy path through the real UI — odds selection, stake entry,
payout calculation, placement and the success receipt — the single highest-value journey
to keep green.
"""

import allure
import pytest

from utils.api.api_balance import get_balance
from utils.common.common_variables import Selection

STAKE = 10


@allure.epic("Single Bet Placement")
@allure.feature("Place bet (UI)")
@allure.story("Happy path")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A user can place a single bet and see the success receipt")
@allure.description(
    "Drives the real browser through the critical journey: select the HOME odds on "
    "the first match, enter a stake, confirm the slip payout equals stake x odds, "
    "place the bet and assert the receipt shows a Bet ID, the stake and the odds."
)
@allure.testcase("tc-01", "TC-01: Place a valid single bet (happy path)")
@allure.issue("bug-03", "BUG-03: UI balance does not refresh after placing a bet")
@pytest.mark.ui
def test_user_can_place_a_single_bet(match_list_page, first_match):
    odds = first_match.odds.home
    start_balance = get_balance().json()["balance"]
    with allure.step(f"Select the HOME outcome on '{first_match.id}'"):
        match_list_page.select_outcome(first_match.id, Selection.HOME)

    slip = match_list_page.bet_slip()
    with allure.step(f"Enter a stake of {STAKE}"):
        slip.enter_stake(str(STAKE))

    with allure.step("The slip payout equals stake x odds"):
        assert slip.potential_payout() == f"€{STAKE * odds:.2f}"

    with allure.step("Place the bet"):
        receipt = slip.place_bet()

    with allure.step("The button shows the 'Placing...' loading state"):
        slip.wait_until_placing()

    with allure.step("Wait for the success receipt"):
        receipt.wait_until_visible()
        allure.attach(
            match_list_page.driver.get_screenshot_as_png(),
            name="success-receipt",
            attachment_type=allure.attachment_type.PNG,
        )

    with allure.step("The receipt shows a Bet ID, the stake and the odds"):
        assert receipt.is_displayed()
        assert receipt.bet_id().startswith("#B-")
        details = receipt.details_text()
        assert f"€{STAKE:.2f}" in details
        assert f"{odds:.2f}" in details

    with allure.step("Close the modal"):
        receipt.close()

    with allure.step("The header balance is reduced by the stake"):
        # Expected to FAIL: the UI balance does not refresh after a bet (BUG-03).
        # We still wait, giving the header a fair chance to re-render.
        assert match_list_page.wait_balance_equals(
            start_balance - STAKE
        ), f"header balance did not update to {start_balance - STAKE}"
