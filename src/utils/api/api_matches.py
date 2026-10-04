"""API helpers for GET /api/matches."""

from requests import Response, get

from utils.common.common_variables import ApiEndpoint
from utils.common.http_helper import create_url, fetch_and_log_response


def get_matches(user_id: str | None = None, **kwargs) -> Response:
    """Return the upcoming-match list."""
    return fetch_and_log_response(
        create_url(ApiEndpoint.MATCHES.value),
        get,
        user_id=user_id,
        **kwargs,
    )
