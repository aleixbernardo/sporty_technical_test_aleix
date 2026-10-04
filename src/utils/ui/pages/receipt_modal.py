"""Page object for the success receipt modal shown after a bet is placed."""

from selenium.webdriver.common.by import By

from utils.ui.pages.base_page import BasePage

# Placement goes through a 'PLACING...' state and can take a few seconds to resolve.
RECEIPT_TIMEOUT = 25


class ReceiptModal(BasePage):
    _ROOT = (By.ID, "modal-success")
    _BET_ID = (By.ID, "modal-success-bet-id")
    _CLOSE = (By.ID, "modal-success-close")

    def wait_until_visible(self) -> "ReceiptModal":
        self.wait._timeout = RECEIPT_TIMEOUT
        self._visible(self._ROOT)
        return self

    def is_displayed(self) -> bool:
        return self._visible(self._ROOT).is_displayed()

    def bet_id(self) -> str:
        return self._visible(self._BET_ID).text

    def details_text(self) -> str:
        """Full text of the receipt (match, stake, odds, payout, timestamp)."""
        return self._visible(self._ROOT).text

    def close(self) -> None:
        self._click(self._CLOSE)
