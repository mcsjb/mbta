"""Repository for fetching and processing subway data from MBTA API."""

from collections import defaultdict

from mbta_client.client import MBTAClient
from models.subway_models import SubwayData, StopConnection, ConnectedStop


class SubwayRepository:
    """Handles all data access and transformation for subway system data."""

    def __init__(self, client: MBTAClient):
        self.client = client

    def load_subway_data(self) -> SubwayData:
        """
        Load all subway data needed for analysis.

        This method:
        1. Fetches all subway routes (route types 0 and 1)
        2. Fetches stops for each route
        3. Builds a connectivity graph showing which stops connect to which other stops
        """
        routes = self._fetch_subway_routes()
        route_stops = self._fetch_stops(routes)
        subway_graph = self._build_connectivity_graph(route_stops)

        return SubwayData(
            routes=routes,
            route_stops=route_stops,
            subway_graph=subway_graph,
        )

    def _fetch_subway_routes(self) -> list:
        """
        Fetch subway routes (types 0 and 1).

        Route type 0: Light rail (Green Line)
        Route type 1: Heavy rail (Red, Orange, Blue Lines)
        """
        subway_route_types = [0, 1]
        response = self.client.get_routes(route_types=subway_route_types)
        return response.data

    def _fetch_stops(self, routes: list) -> dict[str, list[ConnectedStop]]:
        """
        Fetch stops for each route.
        returns mapping of route_id to list of ConnectedStop(stop_name, [route_ids]) for that route
        """
        route_stops = {}
        for route in routes:
            stops_response = self.client.get_stops(route_ids=[route.id])
            route_stops[route.id] = [
                ConnectedStop(stop.attributes.name, [route.id])
                for stop in stops_response.data
            ]
        return route_stops

    def _build_connectivity_graph(
        self, route_stops: dict[str, list[ConnectedStop]]
    ) -> dict[str, list[StopConnection]]:
        """
        Build a graph showing which stops connect to which other stops via which routes.

        For each route, every stop can reach every other stop on that route.
        If multiple routes serve the same stop pair, all routes are included.
        """
        subway_map = defaultdict(lambda: defaultdict(set))

        for route_id, stops in route_stops.items():
            # Each stop on this route can reach every other stop on this route
            # When we start caring about efficiency, do we do this with routes as nodes instead of stops?
            # Routes as nodes with connecting stops as lines between them,
            # smaller tree to traverse, and instead of node==requested_stop, it would be requested_stop in node.stops
            # with final instructions being "for node,edge in path: {node.green line} to {edge.stop_name} finally ride {node.red line} to get to {requested_stop}"
            for connected_stop in stops:
                for other_connected_stop in stops:
                    if (
                        connected_stop.stop_name != other_connected_stop.stop_name
                    ):  # do not map stop to itself
                        subway_map[connected_stop.stop_name][
                            other_connected_stop.stop_name
                        ].add(route_id)

        # Convert sets to lists and use StopConnection objects
        return {
            stop_name: [
                StopConnection(stop=connected_stop, routes=list(routes))
                for connected_stop, routes in connections.items()
            ]
            for stop_name, connections in subway_map.items()
        }
