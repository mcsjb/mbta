"""
pydantic models representing expected response of MBTA API requests used for project
Used to validate API response to quickly validate return structure
"""

from pydantic import BaseModel
from typing import List, Optional


class StopAttributes(BaseModel):
    name: str


class StopData(BaseModel):
    id: str
    attributes: StopAttributes


class StopsResponse(BaseModel):
    data: List[StopData]


class RouteAttributes(BaseModel):
    color: str
    description: str
    direction_destinations: List[str]
    direction_names: List[str]
    fare_class: str
    listed_route: bool
    long_name: str
    short_name: str
    sort_order: int
    text_color: str
    type: int


class RouteLinks(BaseModel):
    self: str


class RelationshipData(BaseModel):
    id: str
    type: str


class Relationship(BaseModel):
    data: Optional[RelationshipData]


class RouteRelationships(BaseModel):
    agency: Relationship
    line: Relationship


class RouteData(BaseModel):
    id: str
    type: str
    attributes: RouteAttributes
    links: RouteLinks
    relationships: RouteRelationships


class RoutesResponse(BaseModel):
    data: List[RouteData]


class RelationshipDataList(BaseModel):
    data: List[RelationshipData]
