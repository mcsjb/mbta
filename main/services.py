import logging
from collections import defaultdict
from mbta_client.client import MBTAClient
from models.subway_models import SubwayData

logger = logging.getLogger(__name__)


class BroadQuestionService:
    """Service to interact with MBTA data through repository

    Answers 3 sets of questions based on publicly available information via MBTA API
    1. List long names of all subway routes
    2. Extend your program so it displays the following additional information about the commuter rail:
        - The name of the subway route with he most stops as well as a count of its stops
        - The name of the subway route with the fewest stops as well as a count of its stops
        - A list of the stops that connect two or more subway routes along with
    3. Take two stops on the subway routes, list a rail route you could travel to get from one stop to the other
    """

    def __init__(self, client: MBTAClient, repository=None):
        self._client = client
        self._repository = repository
        self.subway_map: SubwayData = self._repository.load_subway_data()

    def answer_all_questions(self, start_stop: str, final_stop: str):
        self.log_subway_routes()
        self.log_route_and_stop_info()
        self.log_path_for_stops(start=start_stop, stop=final_stop)

    def log_subway_routes(self):
        """
        List long names of all subway routes
        Subway routes are represented by route type 0, 1

        Note: Use API to filter on only subway routes, all questions only needed subway routes, so filter early
        Less data across the network, less data to process client side.
        """
        subway_routes = self.subway_map.routes
        logger.info("=" * 60)
        logger.info("QUESTION 1: Subway Routes")
        logger.info("=" * 60)
        for route in subway_routes:
            logger.info(f"  • {route.attributes.long_name}")

    def log_route_and_stop_info(self):
        """
        Extend your program so it displays the following additional information about the commuter rail:
        - The name of the subway route with he most stops as well as a count of its stops
        - The name of the subway route with the fewest stops as well as a count of its stops
        - A list of the stops that connect two or more subway routes along with the relevant route names for each stop
        """
        # Get all subway routes and their stops
        subway_route_stops = self.subway_map.route_stops
        # Get stop counts per route
        route_lengths = {r: len(stops) for r, stops in subway_route_stops.items()}
        # Find max and min stop counts
        max_stops = max(route_lengths.values())
        min_stops = min(route_lengths.values())
        # Find routes with the min and max values - so that we report ties at top and bottom
        most_stops_routes = [
            r for r, length in route_lengths.items() if length == max_stops
        ]
        fewest_stops_routes = [
            r for r, length in route_lengths.items() if length == min_stops
        ]

        # for part 2 of the question - find stops that connect two or more routes, look at the subway route
        # and extract any stops associated > 1 route in SubwayMap.StopConnection

        stop_routes = defaultdict(set)
        route_stops = self.subway_map.route_stops
        # reverse our mapping of routes -> stops to stop -> routes for quick reference to stops > 1 route
        for route, stops in route_stops.items():
            for stop in stops:
                stop_routes[stop.stop_name].add(route)

        # Now stop_routes[stop] contains all routes passing through this stop
        connecting_stops = [
            (stop, routes) for stop, routes in stop_routes.items() if len(routes) > 1
        ]
        self._log_question_two(
            most_stops_routes=most_stops_routes,
            fewest_stops_routes=fewest_stops_routes,
            max_stops=max_stops,
            min_stops=min_stops,
            connecting_stops=connecting_stops,
            subway_route_stops=subway_route_stops,
        )

    def _log_question_two(
        self,
        most_stops_routes,
        fewest_stops_routes,
        max_stops,
        min_stops,
        connecting_stops,
        subway_route_stops,
    ):

        def log_routes(label: str, routes: list[str], stop_count: int):
            """Log routes with their stops grouped by 5."""
            for route in routes:
                stop_names = [stop.stop_name for stop in subway_route_stops[route]]
                logger.info(f"{label}: {route} ({stop_count} stops)")
                logger.info("  Stops:")
                for i in range(0, len(stop_names), 5):
                    logger.info(f"    {', '.join(stop_names[i:i + 5])}")

        logger.info("")
        logger.info("=" * 60)
        logger.info("QUESTION 2: Route Statistics")
        logger.info("=" * 60)

        log_routes("Route(s) with most stops", most_stops_routes, max_stops)
        logger.info("")
        log_routes("Route(s) with fewest stops", fewest_stops_routes, min_stops)

        logger.info("")
        if connecting_stops:
            logger.info("")
            logger.info(f"Transfer Stations ({len(connecting_stops)} total):")
            logger.info("-" * 60)

            # Find longest stop name for alignment
            max_stop_length = max(len(stop) for stop, _ in connecting_stops)

            for stop, routes in sorted(connecting_stops):
                # Right-align routes with dots for visual separation
                padding = "." * (max_stop_length - len(stop) + 2)
                route_list = ", ".join(sorted(routes))
                logger.info(f"  {stop} {padding} [{route_list}]")
        else:
            logger.info("")
            logger.info("No stops connect multiple routes.")

    def log_path_for_stops(self, start, stop):
        """
        Given a subway map (stop_name -> list of connections), a start stop, and a final stop, find a path from start to stop
        Limited Optimization, prioritizes staying on current route over switching
        """

        subway_map = self.subway_map.subway_graph
        if start not in subway_map:
            logger.error(f"Start stop '{start}' not found in subway map.")
            return []
        if stop not in subway_map:
            logger.error(f"Final stop '{stop}' not found in subway map.")
            return []
        visited = set()
        path_traveled = [(start, [], [])]  # (current_stop, stops_path, routes_path)
        found_path = None
        found_stops = None

        while path_traveled:
            current_stop, stops_path, routes_path = path_traveled.pop(0)
            if current_stop == stop:
                found_path = routes_path
                found_stops = stops_path + [current_stop]
                break
            if current_stop in visited:
                continue
            visited.add(current_stop)

            for connection in subway_map.get(current_stop, []):
                next_stop = connection.stop
                next_routes = connection.routes

                current_route = routes_path[-1] if routes_path else None

                # Sort routes to prioritize current route
                sorted_routes = sorted(
                    next_routes, key=lambda r: (r != current_route, r)
                )

                for route in sorted_routes:
                    path_traveled.append(
                        (next_stop, stops_path + [current_stop], routes_path + [route])
                    )

        if found_path and found_stops:
            logger.info("")
            logger.info("=" * 60)
            logger.info(f"QUESTION 3: Route from {start} to {stop}")
            logger.info("=" * 60)
            for i in range(len(found_stops) - 1):
                from_stop = found_stops[i]
                to_stop = found_stops[i + 1]
                route = found_path[i]
                logger.info(f"  {from_stop} --[{route}]--> {to_stop}")
