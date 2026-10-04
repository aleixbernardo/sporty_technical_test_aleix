"""
Factory for the Selenium Chrome WebDriver used by the UI tests.
"""

from os import getenv

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

WINDOW_SIZE = "1400,1000"


def _is_headless() -> bool:
    return getenv("HEADLESS", "true").strip().lower() != "false"


def build_driver() -> webdriver.Chrome:
    """Create a configured Chrome WebDriver instance."""
    options = Options()
    if _is_headless():
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE}")
    # Stability flags for CI / containers (no-ops on a local desktop):
    # --no-sandbox: Chrome won't start under the root user used by CI runners.
    # --disable-dev-shm-usage: use /tmp instead of the tiny /dev/shm, avoiding crashes.
    # --disable-gpu: no GPU on headless CI machines.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)
