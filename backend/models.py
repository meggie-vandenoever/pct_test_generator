from pydantic import BaseModel
from typing import List


class Vertex(BaseModel):
    """
    represents a vertex in a flowchart with its position
    """
    label: str
    x: float
    y: float
    
    @property
    def vertex_id(self) -> str:
        return f"{self.label}@({self.x:.0f},{self.y:.0f})"


class Edge(BaseModel):
    """
    represents a single edge in a flowchart
    """
    source: str
    label: str
    target: str


class Flowchart(BaseModel):
    """
    represents a complete flowchart as a list of edges and vertices
    """
    edges: List[Edge]
    vertices: List[Vertex]
