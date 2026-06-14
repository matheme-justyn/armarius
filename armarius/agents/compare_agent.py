"""Compare agent for cross-document comparison."""

from typing import Dict, Any, List
from pathlib import Path
from armarius.agents.base import Agent, AgentContext
from armarius.parser import PDFParser
from armarius.storage import VectorStore


class CompareAgent(Agent):
    """Agent for comparing content across multiple documents."""
    
    def __init__(self, vector_store: VectorStore):
        super().__init__("CompareAgent")
        self.vector_store = vector_store
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        self.log(f"Comparing documents for: {context.query}")
        
        chunks_to_compare = context.intermediate_results.get("chunks", [])
        
        if len(chunks_to_compare) < 2:
            return {
                "comparison": "Need at least 2 chunks to compare",
                "chunks": chunks_to_compare,
            }
        
        comparison_result = self._compare_chunks(chunks_to_compare)
        
        return {
            "comparison": comparison_result,
            "chunks_compared": len(chunks_to_compare),
        }
    
    def _compare_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        pdfs = set(c["pdf_path"] for c in chunks)
        pages = set(c["page"] for c in chunks)
        
        differences = []
        for i, chunk_a in enumerate(chunks):
            for chunk_b in chunks[i+1:]:
                if chunk_a["pdf_path"] != chunk_b["pdf_path"]:
                    differences.append({
                        "source_a": {
                            "pdf": chunk_a["pdf_path"],
                            "page": chunk_a["page"],
                            "text": chunk_a["text"][:200],
                        },
                        "source_b": {
                            "pdf": chunk_b["pdf_path"],
                            "page": chunk_b["page"],
                            "text": chunk_b["text"][:200],
                        },
                    })
        
        return {
            "pdfs_involved": list(pdfs),
            "pages_involved": list(pages),
            "cross_document_pairs": len(differences),
            "differences": differences[:5],
        }
    
    def generate_visual_comparison(
        self,
        chunk_a: Dict[str, Any],
        chunk_b: Dict[str, Any],
        output_dir: Path,
    ) -> Dict[str, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        
        screenshots = {}
        
        for label, chunk in [("a", chunk_a), ("b", chunk_b)]:
            pdf_path = Path(chunk["pdf_path"])
            if not pdf_path.exists():
                continue
            
            parser = PDFParser(pdf_path)
            
            from armarius.parser.pdf_parser import BoundingBox
            bbox = BoundingBox(
                x0=chunk["bbox"]["x0"],
                y0=chunk["bbox"]["y0"],
                x1=chunk["bbox"]["x1"],
                y1=chunk["bbox"]["y1"],
                page=chunk["page"],
            )
            
            screenshot_path = output_dir / f"compare_{label}_{chunk['page']}.png"
            parser.generate_screenshot(bbox, screenshot_path)
            parser.close()
            
            screenshots[label] = str(screenshot_path)
        
        return screenshots
