"""Query agent for semantic search and retrieval."""

from typing import Dict, Any, List
from armarius.agents.base import Agent, AgentContext
from armarius.storage import SemanticSearch, SearchQuery


class QueryAgent(Agent):
    """Agent for semantic search across indexed PDFs."""
    
    def __init__(self, search_service: SemanticSearch):
        super().__init__("QueryAgent")
        self.search = search_service
    
    def execute(self, context: AgentContext) -> Dict[str, Any]:
        self.log(f"Searching for: {context.query}")
        
        search_query = SearchQuery(
            text=context.query,
            top_k=10,
        )
        
        results = self.search.search(search_query)
        
        self.log(f"Found {len(results)} results")
        
        chunks = [
            {
                "text": r.chunk.text,
                "pdf_path": r.chunk.pdf_path,
                "page": r.chunk.bbox.page,
                "bbox": r.chunk.bbox.to_dict(),
                "score": r.score,
                "chunk_id": r.chunk_id,
            }
            for r in results
        ]
        
        return {
            "chunks": chunks,
            "count": len(chunks),
        }
    
    def search_by_pdf(
        self, 
        query: str, 
        pdf_path: str, 
        top_k: int = 10
    ) -> Dict[str, Any]:
        search_query = SearchQuery(
            text=query,
            top_k=top_k,
            pdf_path=pdf_path,
        )
        
        results = self.search.search(search_query)
        
        chunks = [
            {
                "text": r.chunk.text,
                "pdf_path": r.chunk.pdf_path,
                "page": r.chunk.bbox.page,
                "bbox": r.chunk.bbox.to_dict(),
                "score": r.score,
                "chunk_id": r.chunk_id,
            }
            for r in results
        ]
        
        return {
            "chunks": chunks,
            "count": len(chunks),
        }
