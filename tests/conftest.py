"""Shared pytest fixtures for the API and UI test suites."""

import allure
import pytest

from schemas.match import Match
from utils.api.api_matches import get_matches
from utils.api.api_reset_balance import reset_balance
from utils.common.common_variables import HttpStatus
from utils.common.http_helper import get_base_url, get_user_id
from utils.ui.driver_factory import build_driver
from utils.ui.pages.match_list_page import MatchListPage


@pytest.fixture(scope="session")
def base_url() -> str:
    return get_base_url()


@pytest.fixture(scope="session")
def user_id() -> str:
    return get_user_id()


@pytest.fixture
def fresh_balance():
    """Reset the user's balance to a known baseline before a test."""
    response = reset_balance()
    assert response.status_code == HttpStatus.OK, response.text


@pytest.fixture
def first_match() -> Match:
    """Return the first match from the catalogue, validated against the schema."""
    response = get_matches()
    assert response.status_code == HttpStatus.OK, response.text
    matches = response.json()
    assert matches, "GET /api/matches returned an empty list"
    return Match(**matches[0])


@pytest.fixture(scope="session")
def driver():
    """One Chrome WebDriver for the whole session.

    Auth is carried in the URL (`?user-id=`), not cookies, and each UI test reloads
    the page via `match_list_page`, so a single browser can be safely reused across
    tests — much faster than launching one per test.
    """
    instance = build_driver()
    yield instance
    instance.quit()


@pytest.fixture
def match_list_page(driver, base_url, user_id, fresh_balance) -> MatchListPage:
    """Open the app on the match list with a freshly reset balance."""
    return MatchListPage(driver).load(base_url, user_id)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a screenshot to the Allure report when a UI test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        driver = item.funcargs.get("driver")
        if driver is not None:
            allure.attach(
                driver.get_screenshot_as_png(),
                name="screenshot-on-failure",
                attachment_type=allure.attachment_type.PNG,
            )
