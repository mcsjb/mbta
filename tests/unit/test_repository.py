import pytest
from unittest.mock import Mock, MagicMock

from models.subway_models import ConnectedStop, StopConnection, SubwayData
from repositories.subway_repository import SubwayRepository


@pytest.fixture
def mock_client():
    """Mock MBTA client."""
    return Mock()


@pytest.fixture
def repository(mock_client):
    """SubwayRepository instance with mocked client."""
    return SubwayRepository(mock_client)


@pytest.fixture
def sample_route_data():
    """Sample route data from API."""
    route1 = Mock()
    route1.id = "Red"
    route1.attributes = Mock(long_name="Red Line")

    route2 = Mock()
    route2.id = "Blue"
    route2.attributes = Mock(long_name="Blue Line")

    return [route1, route2]


@pytest.fixture
def sample_stops_data():
    """Sample stops data from API."""
    # Red Line stops
    stop1 = Mock()
    stop1.id = "place-alfcl"
    stop1.attributes = Mock()
    stop1.attributes.name = "Alewife"

    stop2 = Mock()
    stop2.id = "place-davis"
    stop2.attributes = Mock()
    stop2.attributes.name = "Davis"

    stop3 = Mock()
    stop3.id = "place-portr"
    stop3.attributes = Mock()
    stop3.attributes.name = "Porter"

    # Blue Line stops
    stop4 = Mock()
    stop4.id = "place-wondl"
    stop4.attributes = Mock()
    stop4.attributes.name = "Wonderland"

    stop5 = Mock()
    stop5.id = "place-gover"
    stop5.attributes = Mock()
    stop5.attributes.name = "Government Center"

    return {
        "Red": [stop1, stop2, stop3],
        "Blue": [stop4, stop5],
    }


class TestSubwayRepositoryInit:
    """Tests for SubwayRepository initialization."""

    def test_init_stores_client(self, mock_client):
        repository = SubwayRepository(mock_client)
        assert repository.client == mock_client


class TestFetchRoutes:
    """Tests for _fetch_routes method."""

    def test_fetches_routes_with_correct_types(
        self, repository, mock_client, sample_route_data
    ):
        mock_response = Mock()
        mock_response.data = sample_route_data
        mock_client.get_routes.return_value = mock_response

        result = repository._fetch_subway_routes()

        mock_client.get_routes.assert_called_once_with(route_types=[0, 1])
        assert result == sample_route_data

    def test_returns_empty_list_when_no_routes(self, repository, mock_client):
        mock_response = Mock()
        mock_response.data = []
        mock_client.get_routes.return_value = mock_response

        result = repository._fetch_subway_routes()

        assert result == []


class TestFetchStops:
    """Tests for _fetch_stops method."""

    def test_fetches_stops_for_each_route(
        self, repository, mock_client, sample_route_data, sample_stops_data
    ):
        # Setup mock responses for each route
        def get_stops_side_effect(route_ids):
            route_id = route_ids[0]
            mock_response = Mock()
            mock_response.data = sample_stops_data.get(route_id, [])
            return mock_response

        mock_client.get_stops.side_effect = get_stops_side_effect

        result = repository._fetch_stops(sample_route_data)

        # Verify get_stops was called for each route
        assert mock_client.get_stops.call_count == 2
        mock_client.get_stops.assert_any_call(route_ids=["Red"])
        mock_client.get_stops.assert_any_call(route_ids=["Blue"])

        # Verify result structure
        assert "Red" in result
        assert "Blue" in result
        assert len(result["Red"]) == 3
        assert len(result["Blue"]) == 2

    def test_creates_connected_stop_objects(
        self, repository, mock_client, sample_route_data, sample_stops_data
    ):
        def get_stops_side_effect(route_ids):
            route_id = route_ids[0]
            mock_response = Mock()
            mock_response.data = sample_stops_data.get(route_id, [])
            return mock_response

        mock_client.get_stops.side_effect = get_stops_side_effect

        result = repository._fetch_stops(sample_route_data)

        # Verify ConnectedStop objects are created correctly
        red_stops = result["Red"]
        assert isinstance(red_stops[0], ConnectedStop)
        assert red_stops[0].stop_name == "Alewife"
        assert red_stops[0].route_names == ["Red"]

    def test_handles_route_with_no_stops(self, repository, mock_client):
        route = Mock()
        route.id = "Orange"

        mock_response = Mock()
        mock_response.data = []
        mock_client.get_stops.return_value = mock_response

        result = repository._fetch_stops([route])

        assert result["Orange"] == []


class TestBuildConnectivityGraph:
    """Tests for _build_connectivity_graph method."""

    def test_builds_graph_with_single_route(self, repository):
        route_stops = {
            "Red": [
                ConnectedStop("Alewife", ["Red"]),
                ConnectedStop("Davis", ["Red"]),
                ConnectedStop("Porter", ["Red"]),
            ]
        }

        result = repository._build_connectivity_graph(route_stops)

        # Each stop should connect to all other stops
        assert "Alewife" in result
        assert "Davis" in result
        assert "Porter" in result

        # Alewife should connect to Davis and Porter
        alewife_connections = result["Alewife"]
        assert len(alewife_connections) == 2
        connection_stops = {conn.stop for conn in alewife_connections}
        assert connection_stops == {"Davis", "Porter"}

    def test_builds_graph_with_multiple_routes(self, repository):
        route_stops = {
            "Red": [
                ConnectedStop("Park Street", ["Red"]),
                ConnectedStop("Alewife", ["Red"]),
            ],
            "Green": [
                ConnectedStop("Park Street", ["Green"]),
                ConnectedStop("Lechmere", ["Green"]),
            ],
        }

        result = repository._build_connectivity_graph(route_stops)

        # Park Street should have connections via both routes
        park_connections = result["Park Street"]
        assert len(park_connections) == 2

        # Check that connections include the correct routes
        for conn in park_connections:
            if conn.stop == "Alewife":
                assert "Red" in conn.routes
            elif conn.stop == "Lechmere":
                assert "Green" in conn.routes

    def test_stop_does_not_connect_to_itself(self, repository):
        route_stops = {
            "Red": [
                ConnectedStop("Alewife", ["Red"]),
                ConnectedStop("Davis", ["Red"]),
            ]
        }

        result = repository._build_connectivity_graph(route_stops)

        # Verify Alewife doesn't connect to itself
        alewife_connections = result["Alewife"]
        connection_stops = {conn.stop for conn in alewife_connections}
        assert "Alewife" not in connection_stops

    def test_handles_empty_route_stops(self, repository):
        route_stops = {}

        result = repository._build_connectivity_graph(route_stops)

        assert result == {}

    def test_handles_single_stop_route(self, repository):
        route_stops = {"Red": [ConnectedStop("Alewife", ["Red"])]}

        result = repository._build_connectivity_graph(route_stops)

        # Single stop has no connections
        assert "Alewife" not in result or len(result["Alewife"]) == 0


class TestLoadSubwayData:
    """Tests for load_subway_data method."""

    def test_loads_complete_subway_data(self, repository, mock_client):
        # Mock route data
        route = Mock()
        route.id = "Red"
        route.attributes = Mock()
        route.attributes.long_name = "Red Line"

        routes_response = Mock()
        routes_response.data = [route]
        mock_client.get_routes.return_value = routes_response

        # Mock stops data
        stop1 = Mock()
        stop1.id = "place-alfcl"
        stop1.attributes = Mock()
        stop1.attributes.name = "Alewife"

        stop2 = Mock()
        stop2.id = "place-davis"
        stop2.attributes = Mock()
        stop2.attributes.name = "Davis"

        stops_response = Mock()
        stops_response.data = [stop1, stop2]
        mock_client.get_stops.return_value = stops_response

        result = repository.load_subway_data()

        # Verify result is SubwayData
        assert isinstance(result, SubwayData)
        assert result.routes == [route]
        assert "Red" in result.route_stops
        assert len(result.route_stops["Red"]) == 2
        assert "Alewife" in result.subway_graph
        assert "Davis" in result.subway_graph

    def test_calls_fetch_routes(self, repository, mock_client):
        routes_response = Mock()
        routes_response.data = []
        mock_client.get_routes.return_value = routes_response

        repository.load_subway_data()

        mock_client.get_routes.assert_called_once_with(route_types=[0, 1])

    def test_builds_connectivity_graph_from_fetched_data(self, repository, mock_client):
        # Mock route
        route = Mock()
        route.id = "Red"

        routes_response = Mock()
        routes_response.data = [route]
        mock_client.get_routes.return_value = routes_response

        # Mock stops
        stop1 = Mock()
        stop1.id = "stop-1"
        stop1.attributes = Mock()
        stop1.attributes.name = "Stop A"

        stop2 = Mock()
        stop2.id = "stop-2"
        stop2.attributes = Mock()
        stop2.attributes.name = "Stop B"

        stops_response = Mock()
        stops_response.data = [stop1, stop2]
        mock_client.get_stops.return_value = stops_response

        result = repository.load_subway_data()

        # Verify graph has connections
        assert "Stop A" in result.subway_graph
        assert "Stop B" in result.subway_graph
        assert len(result.subway_graph["Stop A"]) == 1
        assert result.subway_graph["Stop A"][0].stop == "Stop B"


class TestEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_handles_api_returning_no_routes(self, repository, mock_client):
        routes_response = Mock()
        routes_response.data = []
        mock_client.get_routes.return_value = routes_response

        result = repository.load_subway_data()

        assert isinstance(result, SubwayData)
        assert result.routes == []
        assert result.route_stops == {}
        assert result.subway_graph == {}

    def test_handles_route_with_duplicate_stops(self, repository):
        # This shouldn't happen in real API but test robustness
        route_stops = {
            "Red": [
                ConnectedStop("Alewife", ["Red"]),
                ConnectedStop("Davis", ["Red"]),
                ConnectedStop("Davis", ["Red"]),  # Duplicate
            ]
        }

        result = repository._build_connectivity_graph(route_stops)

        # Should still build valid graph
        assert "Alewife" in result
        assert "Davis" in result

    def test_multiple_routes_between_same_stops(self, repository):
        route_stops = {
            "Red": [
                ConnectedStop("Stop A", ["Red"]),
                ConnectedStop("Stop B", ["Red"]),
            ],
            "Blue": [
                ConnectedStop("Stop A", ["Blue"]),
                ConnectedStop("Stop B", ["Blue"]),
            ],
        }

        result = repository._build_connectivity_graph(route_stops)

        # Stop A to Stop B should have both routes
        stop_a_connections = result["Stop A"]
        assert len(stop_a_connections) == 1
        connection_to_b = stop_a_connections[0]
        assert connection_to_b.stop == "Stop B"
        assert set(connection_to_b.routes) == {"Red", "Blue"}
