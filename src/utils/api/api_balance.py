"""API helpers for GET /api/balance."""

from requests import Response, get

from utils.common.common_variables import ApiEndpoint
from utils.common.http_helper import create_url, fetch_and_log_response


def get_balance(user_id: str | None = None, **kwargs) -> Response:
    """Return the user's current balance."""
    return fetch_and_log_response(
        create_url(ApiEndpoint.BALANCE.value),
        get,
        user_id=user_id,
        **kwargs,
    )
