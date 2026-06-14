"""Summarize agent for multi-document synthesis."""

from typing import Dict, Any, List
from armarius.agents.base import Agent, AgentContext


class SummarizeAgent(Agent):
    """Agent for synthesizing information from multiple sources."""
    
    def __init__(self):
        super().__init__("SummarizeAgent")
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        self.log(f"Synthesizing information for: {context.query}")
        
        chunks = context.intermediate_results.get("chunks", [])
        
        if not chunks:
            return {
                "summary": "No information found to summarize",
                "sources": [],
            }
        
        synthesis = self._synthesize_chunks(chunks)
        
        return {
            "summary": synthesis["summary"],
            "sources": synthesis["sources"],
            "chunk_count": len(chunks),
        }
    
    def _synthesize_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        pdfs = {}
        for chunk in chunks:
            pdf = chunk["pdf_path"]
            if pdf not in pdfs:
                pdfs[pdf] = []
            pdfs[pdf].append(chunk)
        
        summary_parts = []
        sources = []
        
        for pdf_path, pdf_chunks in pdfs.items():
            summary_parts.append(
                f"From {Path(pdf_path).name} ({len(pdf_chunks)} sections):"
            )
            
            for chunk in pdf_chunks[:3]:
                text_preview = chunk["text"][:150]
                summary_parts.append(f"  - Page {chunk['page']}: {text_preview}...")
                
                sources.append({
                    "pdf": pdf_path,
                    "page": chunk["page"],
                    "text_preview": text_preview,
                })
        
        summary = "\n".join(summary_parts)
        
        return {
            "summary": summary,
            "sources": sources,
        }
    
    def create_structured_summary(
        self,
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        by_pdf = {}
        for chunk in chunks:
            pdf = chunk["pdf_path"]
            if pdf not in by_pdf:
                by_pdf[pdf] = {
                    "path": pdf,
                    "name": Path(pdf).name,
                    "pages": set(),
                    "chunks": [],
                }
            by_pdf[pdf]["pages"].add(chunk["page"])
            by_pdf[pdf]["chunks"].append(chunk)
        
        for pdf_data in by_pdf.values():
            pdf_data["pages"] = sorted(list(pdf_data["pages"]))
        
        return {
            "total_sources": len(by_pdf),
            "total_chunks": len(chunks),
            "sources": list(by_pdf.values()),
        }


from pathlib import Path
