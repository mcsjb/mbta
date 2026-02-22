import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from requests.adapters import HTTPAdapter
from pydantic import ValidationError

from mbta_client.client import MBTAClient
from mbta_client.config import MBTAConfig
from mbta_client.exceptions import MBTARequestError, MBTAResponseValidationError
from mbta_client.models import StopsResponse, RoutesResponse, StopData, RouteData


@pytest.fixture
def config():
    """Sample MBTA configuration."""
    return MBTAConfig(
        api_key="test-api-key",
        base_url="https://api-v3.mbta.com",
        timeout=10,
        max_retries=3,
        backoff_factor=0.3,
    )


@pytest.fixture
def client(config):
    """MBTAClient instance with test configuration."""
    return MBTAClient(config)


@pytest.fixture
def mock_response():
    """Mock successful HTTP response."""
    response = Mock()
    response.status_code = 200
    response.raise_for_status = Mock()
    return response


class TestMBTAClientInit:
    """Tests for MBTAClient initialization."""

    def test_init_stores_config(self, config):
        client = MBTAClient(config)
        assert client._config == config

    def test_init_creates_session(self, config):
        client = MBTAClient(config)
        assert isinstance(client._session, requests.Session)

    def test_init_sets_headers(self, config):
        client = MBTAClient(config)
        assert client._session.headers["Accept"] == "application/vnd.api+json"
        assert client._session.headers["x-api-key"] == "test-api-key"

    def test_init_configures_retries(self, config):
        with patch.object(MBTAClient, "_configure_retries") as mock_configure:
            client = MBTAClient(config)
            mock_configure.assert_called_once()


class TestConfigureRetries:
    """Tests for _configure_retries method."""

    def test_mounts_adapter_to_https(self, client):
        # Check that an adapter was mounted to https://
        adapter = client._session.get_adapter("https://api-v3.mbta.com")
        assert isinstance(adapter, HTTPAdapter)


class TestGet:
    """Tests for _get method."""

    def test_get_makes_request_with_correct_url(self, client, mock_response):
        mock_response.json.return_value = {"data": []}

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client._get("/test-path")

            mock_get.assert_called_once()
            args, kwargs = mock_get.call_args
            assert args[0] == "https://api-v3.mbta.com/test-path"

    def test_get_includes_params(self, client, mock_response):
        mock_response.json.return_value = {"data": []}

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            params = {"filter[type]": "0,1"}
            client._get("/routes", params=params)

            args, kwargs = mock_get.call_args
            assert kwargs["params"] == params

    def test_get_uses_timeout_from_config(self, client, mock_response, config):
        mock_response.json.return_value = {"data": []}

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client._get("/test-path")

            args, kwargs = mock_get.call_args
            assert kwargs["timeout"] == config.timeout

    def test_get_returns_json_response(self, client, mock_response):
        expected_data = {"data": [{"id": "1"}]}
        mock_response.json.return_value = expected_data

        with patch.object(client._session, "get", return_value=mock_response):
            result = client._get("/test-path")

            assert result == expected_data

    def test_get_raises_for_http_errors(self, client):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch.object(client._session, "get", return_value=mock_response):
            with pytest.raises(MBTARequestError) as exc_info:
                client._get("/test-path")

            assert "Request failed" in str(exc_info.value)

    def test_get_raises_for_connection_errors(self, client):
        with patch.object(
            client._session,
            "get",
            side_effect=requests.ConnectionError("Connection failed"),
        ):
            with pytest.raises(MBTARequestError) as exc_info:
                client._get("/test-path")

            assert "Request failed" in str(exc_info.value)

    def test_get_raises_for_timeout(self, client):
        with patch.object(
            client._session, "get", side_effect=requests.Timeout("Request timed out")
        ):
            with pytest.raises(MBTARequestError) as exc_info:
                client._get("/test-path")

            assert "Request failed" in str(exc_info.value)

    def test_get_raises_for_invalid_json(self, client, mock_response):
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(client._session, "get", return_value=mock_response):
            with pytest.raises(MBTARequestError) as exc_info:
                client._get("/test-path")

            assert "Invalid JSON response" in str(exc_info.value)


class TestGetStops:
    """Tests for get_stops method."""

    def test_get_stops_without_filters(self, client, mock_response):
        mock_data = {"data": [{"id": "place-alfcl", "attributes": {"name": "Alewife"}}]}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            result = client.get_stops()

            assert isinstance(result, StopsResponse)
            assert len(result.data) == 1
            assert result.data[0].id == "place-alfcl"

    def test_get_stops_with_route_filter(self, client, mock_response):
        mock_data = {"data": [{"id": "place-alfcl", "attributes": {"name": "Alewife"}}]}
        mock_response.json.return_value = mock_data

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client.get_stops(route_ids=["Red", "Blue"])

            args, kwargs = mock_get.call_args
            assert kwargs["params"]["filter[route]"] == "Red,Blue"

    def test_get_stops_with_single_route(self, client, mock_response):
        mock_data = {"data": [{"id": "place-alfcl", "attributes": {"name": "Alewife"}}]}
        mock_response.json.return_value = mock_data

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client.get_stops(route_ids=["Red"])

            args, kwargs = mock_get.call_args
            assert kwargs["params"]["filter[route]"] == "Red"

    def test_get_stops_raises_on_validation_error(self, client, mock_response):
        # Invalid data structure
        mock_data = {"data": [{"invalid": "structure"}]}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            with pytest.raises(MBTAResponseValidationError):
                client.get_stops()

    def test_get_stops_logs_validation_error(self, client, mock_response, caplog):
        mock_data = {"data": [{"invalid": "structure"}]}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            with caplog.at_level("ERROR"):
                try:
                    client.get_stops()
                except MBTAResponseValidationError:
                    pass

                assert "Validation Error" in caplog.text

    def test_get_stops_handles_empty_data(self, client, mock_response):
        mock_data = {"data": []}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            result = client.get_stops()

            assert isinstance(result, StopsResponse)
            assert len(result.data) == 0


class TestGetRoutes:
    """Tests for get_routes method."""

    def test_get_routes_without_filters(self, client, mock_response):
        mock_data = {
            "data": [
                {
                    "id": "Red",
                    "type": "route",
                    "attributes": {
                        "color": "DA291C",
                        "description": "Rapid Transit",
                        "direction_destinations": ["Ashmont/Braintree", "Alewife"],
                        "direction_names": ["South", "North"],
                        "fare_class": "Rapid Transit",
                        "listed_route": True,
                        "long_name": "Red Line",
                        "short_name": "",
                        "sort_order": 10010,
                        "text_color": "FFFFFF",
                        "type": 1,
                    },
                    "links": {"self": "/routes/Red"},
                    "relationships": {
                        "agency": {"data": {"id": "1", "type": "agency"}},
                        "line": {"data": {"id": "line-Red", "type": "line"}},
                    },
                }
            ]
        }
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            result = client.get_routes()

            assert isinstance(result, RoutesResponse)
            assert len(result.data) == 1
            assert result.data[0].id == "Red"

    def test_get_routes_with_type_filter(self, client, mock_response):
        mock_data = {
            "data": [
                {
                    "id": "Red",
                    "type": "route",
                    "attributes": {
                        "color": "DA291C",
                        "description": "Rapid Transit",
                        "direction_destinations": ["Ashmont/Braintree", "Alewife"],
                        "direction_names": ["South", "North"],
                        "fare_class": "Rapid Transit",
                        "listed_route": True,
                        "long_name": "Red Line",
                        "short_name": "",
                        "sort_order": 10010,
                        "text_color": "FFFFFF",
                        "type": 1,
                    },
                    "links": {"self": "/routes/Red"},
                    "relationships": {
                        "agency": {"data": {"id": "1", "type": "agency"}},
                        "line": {"data": {"id": "line-Red", "type": "line"}},
                    },
                }
            ]
        }
        mock_response.json.return_value = mock_data

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client.get_routes(route_types=[0, 1])

            args, kwargs = mock_get.call_args
            assert kwargs["params"]["filter[type]"] == "0,1"

    def test_get_routes_with_single_type(self, client, mock_response):
        mock_data = {
            "data": [
                {
                    "id": "Red",
                    "type": "route",
                    "attributes": {
                        "color": "DA291C",
                        "description": "Rapid Transit",
                        "direction_destinations": ["Ashmont/Braintree", "Alewife"],
                        "direction_names": ["South", "North"],
                        "fare_class": "Rapid Transit",
                        "listed_route": True,
                        "long_name": "Red Line",
                        "short_name": "",
                        "sort_order": 10010,
                        "text_color": "FFFFFF",
                        "type": 1,
                    },
                    "links": {"self": "/routes/Red"},
                    "relationships": {
                        "agency": {"data": {"id": "1", "type": "agency"}},
                        "line": {"data": {"id": "line-Red", "type": "line"}},
                    },
                }
            ]
        }
        mock_response.json.return_value = mock_data

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client.get_routes(route_types=[1])

            args, kwargs = mock_get.call_args
            assert kwargs["params"]["filter[type]"] == "1"

    def test_get_routes_raises_on_validation_error(self, client, mock_response):
        mock_data = {"data": [{"invalid": "structure"}]}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            with pytest.raises(MBTAResponseValidationError):
                client.get_routes()

    def test_get_routes_logs_validation_error(self, client, mock_response, caplog):
        mock_data = {"data": [{"invalid": "structure"}]}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            with caplog.at_level("ERROR"):
                try:
                    client.get_routes()
                except MBTAResponseValidationError:
                    pass

                assert "Validation Error" in caplog.text

    def test_get_routes_handles_empty_data(self, client, mock_response):
        mock_data = {"data": []}
        mock_response.json.return_value = mock_data

        with patch.object(client._session, "get", return_value=mock_response):
            result = client.get_routes()

            assert isinstance(result, RoutesResponse)
            assert len(result.data) == 0


class TestClose:
    """Tests for close method."""

    def test_close_closes_session(self, client):
        with patch.object(client._session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_handles_rate_limit_response(self, client, mock_response):
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "429 Rate Limit"
        )

        with patch.object(client._session, "get", return_value=mock_response):
            with pytest.raises(MBTARequestError):
                client._get("/test-path")

    def test_handles_server_error(self, client, mock_response):
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "500 Server Error"
        )

        with patch.object(client._session, "get", return_value=mock_response):
            with pytest.raises(MBTARequestError):
                client._get("/test-path")

    def test_get_stops_with_empty_route_list(self, client, mock_response):
        mock_data = {"data": []}
        mock_response.json.return_value = mock_data

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client.get_stops(route_ids=[])

            args, kwargs = mock_get.call_args
            # Empty list should not add filter param
            assert "filter[route]" not in kwargs.get("params", {})

    def test_get_routes_with_empty_type_list(self, client, mock_response):
        mock_data = {"data": []}
        mock_response.json.return_value = mock_data

        with patch.object(
            client._session, "get", return_value=mock_response
        ) as mock_get:
            client.get_routes(route_types=[])

            args, kwargs = mock_get.call_args
            # Empty list should not add filter param
            assert "filter[type]" not in kwargs.get("params", {})

    def test_custom_config_values(self):
        custom_config = MBTAConfig(
            api_key="custom-key",
            base_url="https://custom.api.com",
            timeout=30,
            max_retries=5,
            backoff_factor=0.5,
        )
        client = MBTAClient(custom_config)

        assert client._config.api_key == "custom-key"
        assert client._config.base_url == "https://custom.api.com"
        assert client._config.timeout == 30
        assert client._config.max_retries == 5
        assert client._config.backoff_factor == 0.5
