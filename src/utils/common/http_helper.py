"""Central HTTP helper for the API tests.

Single choke point for building URLs, injecting the `x-user-id` header and
issuing requests with logging + basic retries, mirroring backend-tests'
`http_helper`. API helpers under `utils/api/` call `fetch_and_log_response`.
"""

from logging import getLogger
from os import getenv
from time import sleep
from typing import Callable

from dotenv import load_dotenv
from requests import Response
from requests.exceptions import ConnectionError as RequestsConnectionError

from utils.common.common_variables import EnvVar, RequestHeader

load_dotenv()
logger = getLogger(__name__)

DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Sentinel: default behaviour is "read x-user-id from the environment".
# Pass user_id=None to omit the header (unauthorized tests) or a string to
# override it (invalid user-context tests).
USER_ID_FROM_ENV = object()


def get_base_url() -> str:
    base_url = getenv(EnvVar.BASE_URL.value)
    if not base_url:
        raise EnvironmentError(
            f"{EnvVar.BASE_URL.value} environment variable is not set."
        )
    base_url = base_url.strip().rstrip("/")
    # Tolerate a BASE_URL without a scheme (e.g. "example.com") by defaulting
    # to https so requests doesn't raise MissingSchema.
    if "://" not in base_url:
        base_url = f"https://{base_url}"
    return base_url


def get_user_id() -> str:
    """Return the `x-user-id` session token from the environment."""
    user_id = getenv(EnvVar.X_USER_ID.value)
    if not user_id:
        raise EnvironmentError(
            f"{EnvVar.X_USER_ID.value} environment variable is not set."
        )
    return user_id


def create_url(path: str, base_url: str | None = None) -> str:
    """Join BASE_URL with an endpoint path."""
    base = (base_url or get_base_url()).rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def get_headers(
    user_id: object | str | None = USER_ID_FROM_ENV,
    additional_headers: dict | None = None,
) -> dict:
    """Build request headers, resolving the `x-user-id` header.

    - user_id=USER_ID_FROM_ENV (default): use X_USER_ID from the environment.
    - user_id=None: omit the header entirely (for 401 tests).
    - user_id=<str>: use that value verbatim (for invalid-context tests).
    """
    headers = dict(additional_headers or {})

    if user_id is USER_ID_FROM_ENV:
        env_value = getenv(EnvVar.X_USER_ID.value)
        if not env_value:
            raise EnvironmentError(
                f"{EnvVar.X_USER_ID.value} environment variable is not set."
            )
        headers[RequestHeader.X_USER_ID.value] = env_value
    elif user_id is not None:
        headers[RequestHeader.X_USER_ID.value] = user_id

    return headers


def fetch_and_log_response(
    url: str,
    method: Callable[..., Response],
    user_id: object | str | None = USER_ID_FROM_ENV,
    additional_headers: dict | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs,
) -> Response:
    """Issue an HTTP request with headers, retries and logging.

    :param method: a requests verb function (get, post, ...).
    :param kwargs: forwarded to the request (json=, data=, params=, ...).
    """
    headers = get_headers(user_id=user_id, additional_headers=additional_headers)

    response = None
    for attempt in range(MAX_RETRIES):
        try:
            response = method(url, headers=headers, timeout=timeout, **kwargs)
            break
        except RequestsConnectionError:
            if attempt == MAX_RETRIES - 1:
                raise
            logger.warning(
                f"Connection error, retrying ({attempt + 2}/{MAX_RETRIES})..."
            )
            sleep(2**attempt)

    logger.info(
        f"{response.request.method} {response.request.url} -> {response.status_code}"
    )
    return response
