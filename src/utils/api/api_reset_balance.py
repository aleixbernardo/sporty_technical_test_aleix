"""API helpers for POST /api/reset-balance."""

from requests import Response, post

from utils.common.common_variables import ApiEndpoint
from utils.common.http_helper import create_url, fetch_and_log_response


def reset_balance(user_id: str | None = None, **kwargs) -> Response:
    """Reset the user's balance to the initial configured value."""
    return fetch_and_log_response(
        create_url(ApiEndpoint.RESET_BALANCE.value),
        post,
        user_id=user_id,
        **kwargs,
    )
