"""
Models transformed from MBTA API data.
Designed to support answering questions in tech screen
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class StopConnection:
    """Represents a connection from one stop to another via specific routes."""

    stop: str
    routes: list[str]


@dataclass
class ConnectedStop:
    """Represents a stop that connects multiple routes."""

    stop_name: str
    route_names: list[str]


@dataclass
class SubwayData:
    """Remodelled MBTA data expected by BroadService"""

    routes: list[Any]  # List of route objects from API
    route_stops: dict[str, list[ConnectedStop]]  # route_id -> [ConnectedStop]
    subway_graph: dict[str, list[StopConnection]]  # stop_name -> [connections]
