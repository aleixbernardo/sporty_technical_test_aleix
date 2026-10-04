"""API helper for POST /api/place-bet."""

from requests import Response, post

from utils.common.common_variables import ApiEndpoint, Selection
from utils.common.http_helper import create_url, fetch_and_log_response


def place_bet(
    match_id: str,
    selection: Selection | str,
    stake: float,
    user_id: str | None = None,
) -> Response:
    """Place a single bet."""
    return fetch_and_log_response(
        create_url(ApiEndpoint.PLACE_BET.value),
        post,
        user_id=user_id,
        json={"matchId": match_id, "selection": selection, "stake": stake},
    )
