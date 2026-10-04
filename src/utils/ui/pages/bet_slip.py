"""Page object for the right-side bet slip component."""

from selenium.webdriver.common.by import By

from utils.common.common_variables import PlaceBetButtonState
from utils.ui.pages.base_page import BasePage
from utils.ui.pages.receipt_modal import ReceiptModal


class BetSlip(BasePage):
    _STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    _PLACE_BET = (By.ID, "bet-slip-place-bet")
    _POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")

    def enter_stake(self, amount: str) -> "BetSlip":
        self._type(self._STAKE_INPUT, amount)
        return self

    def potential_payout(self) -> str:
        """Return the slip's computed payout text (e.g. '€24.50')."""
        return self._visible(self._POTENTIAL_PAYOUT).text

    def place_bet(self) -> ReceiptModal:
        self._click(self._PLACE_BET)
        return ReceiptModal(self.driver)

    def wait_until_placing(self) -> "BetSlip":
        """Wait until Place Bet shows its loading state ('Placing...')."""
        loading = PlaceBetButtonState.LOADING.lower()
        self.wait.until(
            lambda d: loading in d.find_element(*self._PLACE_BET).text.lower()
        )
        return self
