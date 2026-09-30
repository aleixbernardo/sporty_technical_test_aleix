"""Static values from the Single Bet Placement feature spec.

Grouped as Enums so tests reference names instead of magic values,
mirroring the `common_variables` pattern used in backend-tests.
"""

from enum import Enum, IntEnum


class EnvVar(str, Enum):
    """Names of the environment variables read from `.env`."""

    BASE_URL = "BASE_URL"
    X_USER_ID = "X_USER_ID"


class RequestHeader(str, Enum):
    """HTTP header names required by the API."""

    X_USER_ID = "x-user-id"


class ApiEndpoint(str, Enum):
    """API paths (relative to BASE_URL)."""

    MATCHES = "/api/matches"
    BALANCE = "/api/balance"
    PLACE_BET = "/api/place-bet"
    RESET_BALANCE = "/api/reset-balance"
    DOCS = "/api/docs"
    DOCS_JSON = "/api/docs?format=json"


class Selection(str, Enum):
    """Valid bet selections (API contract)."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"


class OddsButton(str, Enum):
    """UI odds-button labels mapped to their selection."""

    HOME = "1"
    DRAW = "X"
    AWAY = "2"


class Currency(str, Enum):
    CODE = "EUR"
    SYMBOL = "€"


class StakeLimit(float, Enum):
    """Per-bet stake limits (EUR) """

    MIN = 1.00
    MAX = 100.00


class OddsLimit(float, Enum):
    MIN = 1.01
    MAX = 1000.00


class StakeRule(IntEnum):
    DECIMAL_PLACES = 2


class HttpStatus(IntEnum):
    """Status codes referenced by the API error classes."""

    OK = 200
    BAD_REQUEST = 400  # malformed payload
    UNAUTHORIZED = 401  # missing/invalid x-user-id
    METHOD_NOT_ALLOWED = 405  # unsupported HTTP method
    CONFLICT = 409  # bet already in progress (same user)
    UNPROCESSABLE_ENTITY = 422  # semantic validation failure
    SERVER_ERROR = 500  # unexpected server failure


class ApiErrorCode(str, Enum):
    """`error` codes returned in API error bodies ({error, message}).

    Confirmed from the OpenAPI spec and live responses.
    """

    # 401 - auth (AuthError)
    MISSING_USER_ID = "missing_user_id"
    INVALID_USER_ID = "invalid_user_id"

    # 400 - malformed payload
    INVALID_REQUEST = "invalid_request"  # body is not a JSON object
    INVALID_JSON = "invalid_json"  # malformed JSON

    # 422 - semantic validation
    INVALID_MATCH_ID = "invalid_match_id"  # matchId missing/invalid
    INVALID_MATCH = "invalid_match"  # match not found in catalog
    INVALID_SELECTION = "invalid_selection"
    INVALID_STAKE_TYPE = "invalid_stake_type"  # not a valid number
    INVALID_STAKE_PRECISION = "invalid_stake_precision"  # > 2 decimals
    INVALID_STAKE_MIN = "invalid_stake_min"  # below minimum
    INVALID_STAKE_MAX = "invalid_stake_max"  # above maximum
    INSUFFICIENT_BALANCE = "insufficient_balance"  # stake exceeds balance


class UiErrorMessage(str, Enum):
    """Minimum expected UI error copy (spec 4.4)."""

    MIN_STAKE = "Minimum stake is €1.00"
    MAX_STAKE = "Maximum stake is €100.00"
    INSUFFICIENT_BALANCE = "Insufficient balance"


class ErrorModal(str, Enum):
    TITLE = "Something went wrong"


class PlaceBetButtonState(str, Enum):
    LOADING = "Placing..."
