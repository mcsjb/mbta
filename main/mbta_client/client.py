import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, List
from pydantic import ValidationError

from .config import MBTAConfig
from .models import StopsResponse, RoutesResponse
from .exceptions import MBTARequestError, MBTAResponseValidationError

logger = logging.getLogger(__name__)


class MBTAClient:
    """
    Wrapper around MBTA API
    Retries with backoff for transient errors (e.g. rate limits, server issues)
    Matches expected response structure with Pydantic models for validation
    """

    def __init__(self, config: MBTAConfig):
        self._config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Accept": "application/vnd.api+json",
                "x-api-key": self._config.api_key,
            }
        )
        self._configure_retries()

    def _configure_retries(self) -> None:
        """retry with backoff for transient errors (e.g. rate limits, server issues)"""
        retry_strategy = Retry(
            total=self._config.max_retries,
            backoff_factor=self._config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)

    def _get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        execute GET request to MBTA API, raise for status errors, return raw JSON response as dict
        """

        url = f"{self._config.base_url}{path}"
        try:
            response = self._session.get(
                url, params=params, timeout=self._config.timeout
            )
            response.raise_for_status()
        except requests.RequestException as exception:
            raise MBTARequestError(f"Request failed: {exception}") from exception

        try:
            return response.json()
        except ValueError as exception:
            raise MBTARequestError("Invalid JSON response") from exception

    def get_stops(
        self,
        route_ids: Optional[List[str]] = None,
        include_list: Optional[List[str]] = None,
    ) -> StopsResponse:
        """return stops from /stops endpoint, optionally filtered by route_ids"""
        params = {}
        if route_ids:
            params["filter[route]"] = ",".join(str(route_id) for route_id in route_ids)

        raw = self._get("/stops", params=params)

        try:
            return StopsResponse.model_validate(raw)
        except ValidationError as exception:
            logger.error(f"Validation Error: {exception}")
            raise MBTAResponseValidationError(str(exception)) from exception

    def get_routes(self, route_types: Optional[List[int]] = None) -> RoutesResponse:
        """return routes from /routes endpoint, optionally filtered by route_types"""
        params = {}
        if route_types:
            params["filter[type]"] = ",".join(
                str(route_type) for route_type in route_types
            )
        raw = self._get("/routes", params=params)

        try:
            return RoutesResponse.model_validate(raw)
        except ValidationError as exception:
            logger.error(f"Validation Error: {exception}")
            raise MBTAResponseValidationError(str(exception)) from exception

    def close(self) -> None:
        self._session.close()
