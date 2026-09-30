"""API helpers for GET /api/balance."""

from requests import Response, get

from utils.common.common_variables import ApiEndpoint
from utils.common.http_helper import (
    USER_ID_FROM_ENV,
    create_url,
    fetch_and_log_response,
)


def get_balance(user_id: object | str | None = USER_ID_FROM_ENV, **kwargs) -> Response:
    """Return the user's current balance."""
    return fetch_and_log_response(
        create_url(ApiEndpoint.BALANCE.value),
        get,
        user_id=user_id,
        **kwargs,
    )
