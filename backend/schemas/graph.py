"""Pydantic schemas for Neo4j Knowledge Graph queries and Impact Analysis."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    properties: dict

    model_config = ConfigDict(from_attributes=True)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: dict

    model_config = ConfigDict(from_attributes=True)


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]

    model_config = ConfigDict(from_attributes=True)


class ImpactAnalysisResponse(BaseModel):
    connected_obligations: list[dict]
    related_regulations: list[dict]
    conflicts: list[dict]
    recommendations: list[dict]
    impacted_policies: list[dict]

    model_config = ConfigDict(from_attributes=True)
