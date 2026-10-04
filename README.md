# Sports Betting — QA Technical Test

Test automation for the **Single Bet Placement** feature of the
[Sports Betting QA app](https://qae-assignment-tau.vercel.app).

The project is split into two parts:

- **Part A — Manual QA & Strategy** (`docs/`): [`test-plan.md`](docs/test-plan.md) (prioritised
  scenarios) and [`bug-report.md`](docs/bug-report.md) (defects found during execution).
- **Part B — Automation** (this framework): a small, layered Selenium + API suite with two
  high-value tests.

## Stack & tooling choices

| Tool | Why |
|------|-----|
| **Python 3.13** | Required stack. |
| **pytest** | Fixtures + parametrisation + clean assertions; the de-facto Python test runner. |
| **Selenium 4** | Required for UI. Selenium Manager auto-resolves the chromedriver, so no binary to pin. |
| **requests** | Lightweight API client; all calls funnel through one HTTP helper. |
| **pydantic v2** | Response schemas validate the API contract (types + shape), not just values. |
| **allure-pytest** | Rich reporting: steps, severity, epic/feature/story, issue/TMS links, screenshots. |
| **python-dotenv** | Loads config/secrets from `.env` so no credentials live in the repo. |
| **black / isort / flake8 / pre-commit** | Formatting and linting to keep the code consistent. |

## Project structure

```
src/
  schemas/                   # pydantic response models (contract validation)
    base_schema.py  match.py  balance.py  place_bet.py
  utils/
    common/
      common_variables.py    # enums for endpoints, selections, limits, error codes
      http_helper.py         # single choke point: URL building, x-user-id header, retries, logging
    api/                     # one helper per endpoint, each returns a requests.Response
      api_matches.py  api_balance.py  api_place_bet.py  api_reset_balance.py
    ui/
      driver_factory.py      # builds the Chrome WebDriver (headless by default)
      pages/                 # Page Object Model
        base_page.py         # shared explicit-wait helpers
        match_list_page.py   # match list + odds selection + header balance
        bet_slip.py          # stake entry, payout, Place Bet
        receipt_modal.py     # success receipt assertions + close
tests/
  conftest.py                # fixtures: base_url, user_id, fresh_balance, first_match, driver, page
  api/test_place_bet_happy_path.py
  ui/test_place_bet_journey.py
docs/                        # Part A deliverables
.github/workflows/ci.yml     # CI
```

### Page Object Model

UI tests never touch raw locators. Each screen/component is a page object that exposes
intent-level methods (`select_outcome`, `enter_stake`, `place_bet`, `wait_until_visible`) and keeps
its locators private. `BasePage` centralises the explicit waits. Because the app is a React build
with hashed class names, locators are text/attribute based, and a `ci_contains` helper handles
labels that CSS renders uppercase (e.g. `PLACE BET`, `CLOSE`).

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -e .            # add '.[dev]' for the linting tools

cp .env.example .env        # then fill in the values
```

`.env`:

```
BASE_URL=https://qae-assignment-tau.vercel.app
X_USER_ID=<your-user-id>
# HEADLESS=false            # optional: watch the browser locally
```

## Running the tests

```bash
pytest                 # everything
pytest tests/api       # API only
pytest tests/ui        # UI only
pytest -m api          # by marker (api / ui)
HEADLESS=false pytest tests/ui   # headed browser
```

Chrome (latest desktop) must be installed; Selenium Manager fetches the matching driver.

## Reporting (Allure)

Every run writes raw results to `allure-results/` (configured in `pyproject.toml`). To view the
report you need the Allure CLI (`brew install allure`):

```bash
pytest                       # produces allure-results/
allure serve allure-results  # builds and opens the report in the browser
```

Or generate a static report:

```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```

The report includes per-test **steps**, **severity**, the **epic / feature / story** tree, links to
the test plan (**TMS**) and the bug report (**issue**), and a **screenshot** attached automatically
when a UI test fails. In CI the `allure-results` folder is uploaded as a build artifact.

## The two automated tests

- **API — `test_place_bet_happy_path.py`**: fetches the catalogue (`first_match` fixture), places a
  bet on the first match and asserts the server computes the payout (`stake × odds`) and debits the
  balance, cross-checked against `GET /api/balance`. Responses are parsed into **pydantic schemas**
  (`src/schemas/`) so the contract shape is validated, not just the values. The core money path.
- **UI (E2E) — `test_place_bet_journey.py`**: the critical user journey — select odds → enter stake
  → verify the slip payout → place the bet → assert the success receipt (Bet ID, stake, odds).

Each test file opens with a docstring explaining why it was chosen. Tests reset the balance via a
fixture for determinism.

## CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push to `main` and on pull
requests: it sets up Python 3.13 and Chrome, installs the package and runs the API and UI suites.
The `X_USER_ID` is provided as a GitHub Actions secret (`secrets.X_USER_ID`); `BASE_URL` and
`HEADLESS=true` are set in the workflow env.
