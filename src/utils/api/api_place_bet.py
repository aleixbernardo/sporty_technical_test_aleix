"""API helpers for POST /api/place-bet."""

from requests import Response, post

from utils.common.common_variables import ApiEndpoint, Selection
from utils.common.http_helper import (
    USER_ID_FROM_ENV,
    create_url,
    fetch_and_log_response,
)


def place_bet(
    match_id: str | None = None,
    selection: Selection | str | None = None,
    stake: float | str | None = None,
    user_id: object | str | None = USER_ID_FROM_ENV,
    request_body: object | None = None,
    **kwargs,
) -> Response:
    """Place a single bet.

    By default builds the request body from `match_id`/`selection`/`stake`.
    Pass `request_body` to send a custom payload (e.g. missing fields, wrong
    types, or a non-object value for malformed-payload tests). For a payload
    that is not valid JSON at all, call `fetch_and_log_response` with `data=`.
    """
    if request_body is None:
        if isinstance(selection, Selection):
            selection = selection.value
        request_body = {
            "matchId": match_id,
            "selection": selection,
            "stake": stake,
        }

    return fetch_and_log_response(
        create_url(ApiEndpoint.PLACE_BET.value),
        post,
        user_id=user_id,
        json=request_body,
        **kwargs,
    )
