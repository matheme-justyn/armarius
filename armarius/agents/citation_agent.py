"""Citation agent for precise citation generation."""

from typing import Dict, Any, List
from pathlib import Path
from armarius.agents.base import Agent, AgentContext, Citation
from armarius.parser import PDFParser


class CitationAgent(Agent):
    """Agent for generating precise citations with visual evidence."""
    
    def __init__(self, screenshot_dir: Path):
        super().__init__("CitationAgent")
        self.screenshot_dir = Path(screenshot_dir)
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        self.log(f"Generating citations for: {context.query}")
        
        chunks = context.intermediate_results.get("chunks", [])
        
        citations = []
        for chunk in chunks:
            citation = self.create_citation(chunk)
            citations.append(citation.to_dict())
        
        return {
            "citations": citations,
            "count": len(citations),
        }
    
    def create_citation(self, chunk: Dict[str, Any]) -> Citation:
        pdf_path = chunk["pdf_path"]
        page = chunk["page"]
        bbox = chunk["bbox"]
        text = chunk["text"]
        
        metadata = self._extract_metadata(pdf_path)
        
        screenshot_path = None
        if Path(pdf_path).exists():
            screenshot_path = self._generate_screenshot(
                pdf_path, page, bbox
            )
        
        return Citation(
            text=text,
            pdf_path=pdf_path,
            page=page,
            bbox=bbox,
            screenshot_path=screenshot_path,
            title=metadata.get("title"),
            authors=metadata.get("authors"),
        )
    
    def _extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        if not Path(pdf_path).exists():
            return {}
        
        try:
            parser = PDFParser(pdf_path)
            metadata = parser.get_metadata()
            parser.close()
            return {
                "title": metadata.get("title") or Path(pdf_path).name,
                "authors": metadata.get("author"),
            }
        except Exception:
            return {"title": Path(pdf_path).name}
    
    def _generate_screenshot(
        self, 
        pdf_path: str, 
        page: int, 
        bbox: Dict[str, float]
    ) -> str:
        parser = PDFParser(pdf_path)
        
        from armarius.parser.pdf_parser import BoundingBox
        bbox_obj = BoundingBox(
            x0=bbox["x0"],
            y0=bbox["y0"],
            x1=bbox["x1"],
            y1=bbox["y1"],
            page=page,
        )
        
        filename = f"{Path(pdf_path).stem}_p{page}_{hash(str(bbox))}.png"
        screenshot_path = self.screenshot_dir / filename
        
        parser.generate_screenshot(bbox_obj, screenshot_path)
        parser.close()
        
        return str(screenshot_path)
    
    def format_citation_text(self, citation: Citation) -> str:
        parts = []
        
        if citation.title:
            parts.append(f"{citation.title}")
        else:
            parts.append(Path(citation.pdf_path).name)
        
        parts.append(f"(page {citation.page})")
        
        if citation.bbox:
            bbox_str = f"bbox({citation.bbox['x0']:.1f}, {citation.bbox['y0']:.1f}, {citation.bbox['x1']:.1f}, {citation.bbox['y1']:.1f})"
            parts.append(bbox_str)
        
        if citation.screenshot_path:
            parts.append(f"📸 {citation.screenshot_path}")
        
        return " ".join(parts)
