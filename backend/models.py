"""
Data models for the flowchart analysis API.

WHAT IS PYDANTIC?
Pydantic is a library for data validation. It ensures that data
coming into your application matches the expected structure.

For example, if the AI returns JSON with a typo in a field name,
Pydantic will catch it and raise an error instead of silently failing.
"""

from pydantic import BaseModel
from typing import List


class Edge(BaseModel):
    """
    Represents a single edge (connection) in a flowchart.
    
    Attributes:
        source: The starting node (e.g., "Is it raining?")
        label: The condition/label on the edge (e.g., "Yes" or "No")
        target: The ending node (e.g., "Take umbrella")
    """
    source: str
    label: str
    target: str


class Flowchart(BaseModel):
    """
    Represents a complete flowchart as a list of edges.
    
    The Gemini AI returns data in this format, which we validate
    using this model.
    """
    edges: List[Edge]
