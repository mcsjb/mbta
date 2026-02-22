import pytest
from unittest.mock import Mock, patch

from models.subway_models import ConnectedStop, StopConnection, SubwayData
from services import BroadQuestionService


@pytest.fixture
def mock_client():
    """Mock MBTA client."""
    return Mock()


@pytest.fixture
def mock_repository():
    """Mock repository."""
    return Mock()


@pytest.fixture
def sample_routes():
    """Sample subway routes for testing."""
    route1 = Mock()
    route1.attributes = Mock(long_name="Red Line")
    route1.id = "Red"

    route2 = Mock()
    route2.attributes = Mock(long_name="Blue Line")
    route2.id = "Blue"

    route3 = Mock()
    route3.attributes = Mock(long_name="Green Line")
    route3.id = "Green"

    return [route1, route2, route3]


@pytest.fixture
def sample_route_stops():
    """Sample route stops mapping for testing."""
    return {
        "Red Line": [
            ConnectedStop("Alewife", ["Red Line"]),
            ConnectedStop("Davis", ["Red Line"]),
            ConnectedStop("Porter", ["Red Line"]),
            ConnectedStop("Harvard", ["Red Line"]),
            ConnectedStop("Park Street", ["Red Line", "Green Line"]),
        ],
        "Blue Line": [
            ConnectedStop("Wonderland", ["Blue Line"]),
            ConnectedStop("Government Center", ["Blue Line", "Green Line"]),
        ],
        "Green Line": [
            ConnectedStop("Lechmere", ["Green Line"]),
            ConnectedStop("Park Street", ["Red Line", "Green Line"]),
            ConnectedStop("Government Center", ["Blue Line", "Green Line"]),
            ConnectedStop("Boylston", ["Green Line"]),
        ],
    }


@pytest.fixture
def sample_subway_graph():
    """Sample connectivity graph for testing."""
    return {
        "Alewife": [StopConnection("Davis", ["Red Line"])],
        "Davis": [
            StopConnection("Alewife", ["Red Line"]),
            StopConnection("Porter", ["Red Line"]),
        ],
        "Porter": [
            StopConnection("Davis", ["Red Line"]),
            StopConnection("Harvard", ["Red Line"]),
        ],
        "Harvard": [
            StopConnection("Porter", ["Red Line"]),
            StopConnection("Park Street", ["Red Line"]),
        ],
        "Park Street": [
            StopConnection("Harvard", ["Red Line"]),
            StopConnection("Boylston", ["Green Line"]),
            StopConnection("Government Center", ["Green Line"]),
        ],
        "Boylston": [StopConnection("Park Street", ["Green Line"])],
        "Government Center": [
            StopConnection("Park Street", ["Green Line"]),
            StopConnection("Wonderland", ["Blue Line"]),
        ],
        "Wonderland": [StopConnection("Government Center", ["Blue Line"])],
        "Lechmere": [StopConnection("Park Street", ["Green Line"])],
    }


@pytest.fixture
def sample_subway_data(sample_routes, sample_route_stops, sample_subway_graph):
    """Sample SubwayData for testing."""
    return SubwayData(
        routes=sample_routes,
        route_stops=sample_route_stops,
        subway_graph=sample_subway_graph,
    )


@pytest.fixture
def service(mock_client, mock_repository, sample_subway_data):
    """BroadQuestionService instance with mocked dependencies."""
    mock_repository.load_subway_data.return_value = sample_subway_data
    return BroadQuestionService(mock_client, mock_repository)


class TestBroadQuestionServiceInit:
    """Tests for BroadQuestionService initialization."""

    def test_init_stores_client(self, mock_client, mock_repository, sample_subway_data):
        mock_repository.load_subway_data.return_value = sample_subway_data
        service = BroadQuestionService(mock_client, mock_repository)
        assert service._client == mock_client

    def test_init_stores_repository(
        self, mock_client, mock_repository, sample_subway_data
    ):
        mock_repository.load_subway_data.return_value = sample_subway_data
        service = BroadQuestionService(mock_client, mock_repository)
        assert service._repository == mock_repository

    def test_init_loads_subway_data(
        self, mock_client, mock_repository, sample_subway_data
    ):
        mock_repository.load_subway_data.return_value = sample_subway_data
        service = BroadQuestionService(mock_client, mock_repository)
        mock_repository.load_subway_data.assert_called_once()
        assert service.subway_map == sample_subway_data


class TestAnswerQuestionOne:
    """Tests for answer_question_one method."""

    def test_logs_all_subway_routes(self, service, sample_routes, caplog):
        with caplog.at_level("INFO"):
            service.log_subway_routes()

        assert "Red Line" in caplog.text
        assert "Blue Line" in caplog.text
        assert "Green Line" in caplog.text

    def test_logs_correct_number_of_routes(self, service, caplog):
        with caplog.at_level("INFO"):
            service.log_subway_routes()

        log_lines = [record for record in caplog.records if "•" in record.message]
        assert len(log_lines) == 3

    def test_handles_empty_routes(self, mock_client, mock_repository):
        empty_subway_data = SubwayData(routes=[], route_stops={}, subway_graph={})
        mock_repository.load_subway_data.return_value = empty_subway_data
        service = BroadQuestionService(mock_client, mock_repository)

        service.log_subway_routes()


class TestAnswerQuestionTwo:
    """Tests for answer_question_two method."""

    def test_identifies_route_with_most_stops(self, service, caplog):
        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        assert "Route(s) with most stops: Red Line (5 stops)" in caplog.text

    def test_identifies_route_with_fewest_stops(self, service, caplog):
        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        assert "Route(s) with fewest stops: Blue Line (2 stops)" in caplog.text

    def test_identifies_connecting_stops(self, service, caplog):
        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        assert "Government Center" in caplog.text
        assert "Park Street" in caplog.text

    def test_connecting_stops_show_correct_routes(self, service, caplog):
        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        log_text = caplog.text
        assert "Park Street" in log_text
        assert "Government Center" in log_text

    def test_handles_tie_for_most_stops(self, mock_client, mock_repository, caplog):
        tied_route_stops = {
            "Red Line": [
                ConnectedStop("Stop1", ["Red Line"]),
                ConnectedStop("Stop2", ["Red Line"]),
                ConnectedStop("Stop3", ["Red Line"]),
            ],
            "Blue Line": [
                ConnectedStop("Stop4", ["Blue Line"]),
                ConnectedStop("Stop5", ["Blue Line"]),
                ConnectedStop("Stop6", ["Blue Line"]),
            ],
        }
        subway_data = SubwayData(
            routes=[],
            route_stops=tied_route_stops,
            subway_graph={},
        )
        mock_repository.load_subway_data.return_value = subway_data
        service = BroadQuestionService(mock_client, mock_repository)

        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        assert "Route(s) with most stops" in caplog.text
        assert "3 stops" in caplog.text

    def test_handles_tie_for_fewest_stops(self, mock_client, mock_repository):
        tied_route_stops = {
            "Red Line": [ConnectedStop("Stop1", ["Red Line"])],
            "Blue Line": [ConnectedStop("Stop2", ["Blue Line"])],
        }
        subway_data = SubwayData(
            routes=[],
            route_stops=tied_route_stops,
            subway_graph={},
        )
        mock_repository.load_subway_data.return_value = subway_data
        service = BroadQuestionService(mock_client, mock_repository)

        service.log_route_and_stop_info()

    def test_no_connecting_stops(self, mock_client, mock_repository, caplog):
        isolated_route_stops = {
            "Red Line": [
                ConnectedStop("Stop1", ["Red Line"]),
                ConnectedStop("Stop2", ["Red Line"]),
            ],
            "Blue Line": [
                ConnectedStop("Stop3", ["Blue Line"]),
                ConnectedStop("Stop4", ["Blue Line"]),
            ],
        }
        subway_data = SubwayData(
            routes=[],
            route_stops=isolated_route_stops,
            subway_graph={},
        )
        mock_repository.load_subway_data.return_value = subway_data
        service = BroadQuestionService(mock_client, mock_repository)

        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        assert "No stops connect multiple routes" in caplog.text


class TestAnswerQuestionThree:
    """Tests for answer_question_three method."""

    def test_finds_direct_path(self, service, caplog):
        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Alewife", "Harvard")

        assert result is None
        assert "Alewife --[Red Line]--> Davis" in caplog.text

    def test_finds_path_with_transfer(self, service, caplog):
        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Harvard", "Wonderland")

        assert "Route from Harvard to Wonderland" in caplog.text
        assert "Harvard --[Red Line]--> Park Street" in caplog.text

    def test_returns_empty_for_invalid_start(self, service, caplog):
        with caplog.at_level("ERROR"):
            result = service.log_path_for_stops("InvalidStop", "Harvard")

        assert result == []
        assert "Start stop 'InvalidStop' not found" in caplog.text

    def test_returns_empty_for_invalid_end(self, service, caplog):
        with caplog.at_level("ERROR"):
            result = service.log_path_for_stops("Alewife", "InvalidStop")

        assert result == []
        assert "Final stop 'InvalidStop' not found" in caplog.text

    def test_same_start_and_end(self, service, caplog):
        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Alewife", "Alewife")

        assert result is None

    def test_path_includes_correct_stops(self, service, caplog):
        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Alewife", "Porter")

        log_text = caplog.text
        assert "Alewife" in log_text
        assert "Davis" in log_text
        assert "Porter" in log_text

    def test_prioritizes_staying_on_same_route(self, service, caplog):
        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Alewife", "Harvard")

        log_text = caplog.text
        assert "Red Line" in log_text
        assert log_text.count("Red Line") >= 3

    def test_handles_disconnected_stops(self, mock_client, mock_repository, caplog):
        disconnected_graph = {
            "Stop1": [StopConnection("Stop2", ["Red Line"])],
            "Stop2": [StopConnection("Stop1", ["Red Line"])],
            "Stop3": [StopConnection("Stop4", ["Blue Line"])],
            "Stop4": [StopConnection("Stop3", ["Blue Line"])],
        }
        subway_data = SubwayData(
            routes=[],
            route_stops={},
            subway_graph=disconnected_graph,
        )
        mock_repository.load_subway_data.return_value = subway_data
        service = BroadQuestionService(mock_client, mock_repository)

        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Stop1", "Stop3")

        assert result is None
        assert "Path from Stop1 to Stop3" not in caplog.text


class TestAnswerAllQuestions:
    """Tests for answer_all_questions method."""

    def test_calls_all_three_question_methods(self, service):
        with patch.object(service, "log_subway_routes") as mock_q1, patch.object(
            service, "log_route_and_stop_info"
        ) as mock_q2, patch.object(service, "log_path_for_stops") as mock_q3:

            service.answer_all_questions("Start", "End")

            mock_q1.assert_called_once()
            mock_q2.assert_called_once()
            mock_q3.assert_called_once_with(start="Start", stop="End")

    def test_passes_correct_parameters_to_question_three(self, service):
        with patch.object(service, "log_subway_routes"), patch.object(
            service, "log_route_and_stop_info"
        ), patch.object(service, "log_path_for_stops") as mock_q3:

            service.answer_all_questions("Alewife", "Harvard")

            mock_q3.assert_called_once_with(start="Alewife", stop="Harvard")

    def test_executes_questions_in_order(self, service):
        call_order = []

        def track_q1():
            call_order.append("q1")

        def track_q2():
            call_order.append("q2")

        def track_q3(start, stop):
            call_order.append("q3")

        with patch.object(
            service, "log_subway_routes", side_effect=track_q1
        ), patch.object(
            service, "log_route_and_stop_info", side_effect=track_q2
        ), patch.object(
            service, "log_path_for_stops", side_effect=track_q3
        ):

            service.answer_all_questions("Start", "End")

            assert call_order == ["q1", "q2", "q3"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_subway_data(self, mock_client, mock_repository):
        empty_data = SubwayData(routes=[], route_stops={}, subway_graph={})
        mock_repository.load_subway_data.return_value = empty_data
        service = BroadQuestionService(mock_client, mock_repository)

        service.log_subway_routes()

    def test_single_route_system(self, mock_client, mock_repository, caplog):
        single_route = Mock()
        single_route.attributes.long_name = "Red Line"

        single_route_data = SubwayData(
            routes=[single_route],
            route_stops={
                "Red Line": [
                    ConnectedStop("Stop1", ["Red Line"]),
                    ConnectedStop("Stop2", ["Red Line"]),
                ]
            },
            subway_graph={"Stop1": [StopConnection("Stop2", ["Red Line"])]},
        )
        mock_repository.load_subway_data.return_value = single_route_data
        service = BroadQuestionService(mock_client, mock_repository)

        with caplog.at_level("INFO"):
            service.log_route_and_stop_info()

        assert "Route(s) with most stops: Red Line (2 stops)" in caplog.text
        assert "Route(s) with fewest stops: Red Line (2 stops)" in caplog.text

    def test_route_with_single_stop(self, mock_client, mock_repository):
        single_stop_data = SubwayData(
            routes=[],
            route_stops={"Red Line": [ConnectedStop("Stop1", ["Red Line"])]},
            subway_graph={},
        )
        mock_repository.load_subway_data.return_value = single_stop_data
        service = BroadQuestionService(mock_client, mock_repository)

        service.log_route_and_stop_info()

    def test_circular_route(self, mock_client, mock_repository, caplog):
        circular_graph = {
            "Stop1": [StopConnection("Stop2", ["Red Line"])],
            "Stop2": [StopConnection("Stop3", ["Red Line"])],
            "Stop3": [StopConnection("Stop1", ["Red Line"])],
        }
        circular_data = SubwayData(
            routes=[],
            route_stops={
                "Red Line": [
                    ConnectedStop("Stop1", ["Red Line"]),
                    ConnectedStop("Stop2", ["Red Line"]),
                    ConnectedStop("Stop3", ["Red Line"]),
                ]
            },
            subway_graph=circular_graph,
        )
        mock_repository.load_subway_data.return_value = circular_data
        service = BroadQuestionService(mock_client, mock_repository)

        with caplog.at_level("INFO"):
            result = service.log_path_for_stops("Stop1", "Stop3")

        assert "Route from Stop1 to Stop3" in caplog.text
        assert "Stop1 --[Red Line]--> Stop2" in caplog.text
