"""Page object for the main match-list screen (header balance + odds buttons)."""

import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from utils.common.common_variables import Selection
from utils.ui.pages.base_page import BasePage
from utils.ui.pages.bet_slip import BetSlip


class MatchListPage(BasePage):
    _BALANCE = (By.ID, "header-balance")

    def load(self, base_url: str, user_id: str) -> "MatchListPage":
        self.driver.get(f"{base_url}/?user-id={user_id}")
        self._visible(self._BALANCE)
        return self

    def balance(self) -> float:
        """Return the balance shown in the header (e.g. 'Balance: €120.00' -> 120.0)."""
        text = self._visible(self._BALANCE).text
        return float(re.search(r"([\d.]+)", text).group(1))

    def wait_balance_equals(
        self, expected: float, timeout: int = 5, tolerance: float = 0.01
    ) -> bool:
        """Poll the header balance until it reaches `expected`.

        Returns True if the balance updates in time, False on timeout — giving the UI
        a fair chance to re-render (e.g. after a bet) without assuming it is instant.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda _: abs(self.balance() - expected) <= tolerance
            )
            return True
        except TimeoutException:
            return False

    def select_outcome(self, match_id: str, selection: Selection) -> "MatchListPage":
        """Click the odds button for `selection` on the given match.

        Odds buttons expose stable ids of the form `odds-<matchId>-<home|draw|away>`,
        so the match is identified by id (fetched from the API) rather than by scraping
        the list.
        """
        self._click((By.ID, f"odds-{match_id}-{selection.lower()}"))
        return self

    def bet_slip(self) -> BetSlip:
        return BetSlip(self.driver)
