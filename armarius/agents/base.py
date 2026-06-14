"""Multi-agent framework for PDF knowledge management."""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path


@dataclass
class AgentContext:
    """Shared context for agent communication."""
    query: str
    intermediate_results: Dict[str, Any]
    active_documents: List[str]
    citations: List[Dict[str, Any]]
    screenshots: List[str]


class Agent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Execute agent task with given context."""
        pass
    
    def log(self, message: str):
        print(f"[{self.name}] {message}")


@dataclass
class Citation:
    """Citation with bounding box and metadata."""
    text: str
    pdf_path: str
    page: int
    bbox: Dict[str, float]
    screenshot_path: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "pdf_path": self.pdf_path,
            "page": self.page,
            "bbox": self.bbox,
            "screenshot_path": self.screenshot_path,
            "title": self.title,
            "authors": self.authors,
        }
