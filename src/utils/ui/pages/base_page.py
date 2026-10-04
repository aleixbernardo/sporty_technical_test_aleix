"""Base class shared by all page objects.

Centralises the WebDriver reference and the common explicit-wait helpers so the
concrete pages only describe locators and intent, not boilerplate.
"""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DEFAULT_TIMEOUT = 15


class BasePage:
    def __init__(self, driver: WebDriver, timeout: int = DEFAULT_TIMEOUT):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)

    def _visible(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _clickable(self, locator: tuple[str, str]) -> WebElement:
        return self.wait.until(EC.element_to_be_clickable(locator))

    def _click(self, locator: tuple[str, str]) -> None:
        self._clickable(locator).click()

    def _type(self, locator: tuple[str, str], text: str) -> None:
        field = self._visible(locator)
        field.clear()
        field.send_keys(text)
