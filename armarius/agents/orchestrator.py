"""Orchestrator for coordinating agent workflows."""

from typing import Dict, Any, List, Optional
from pathlib import Path
from armarius.agents.base import Agent, AgentContext
from armarius.agents.query_agent import QueryAgent
from armarius.agents.compare_agent import CompareAgent
from armarius.agents.summarize_agent import SummarizeAgent
from armarius.agents.citation_agent import CitationAgent


class Orchestrator:
    """Coordinates multi-agent workflows."""
    
    def __init__(
        self,
        query_agent: QueryAgent,
        compare_agent: CompareAgent,
        summarize_agent: SummarizeAgent,
        citation_agent: CitationAgent,
    ):
        self.query_agent = query_agent
        self.compare_agent = compare_agent
        self.summarize_agent = summarize_agent
        self.citation_agent = citation_agent
    
    def process_query(
        self, 
        query: str,
        workflow: str = "search_and_cite"
    ) -> Dict[str, Any]:
        context = AgentContext(
            query=query,
            intermediate_results={},
            active_documents=[],
            citations=[],
            screenshots=[],
        )
        
        if workflow == "search_and_cite":
            return self._search_and_cite(context)
        elif workflow == "compare_and_cite":
            return self._compare_and_cite(context)
        elif workflow == "summarize_and_cite":
            return self._summarize_and_cite(context)
        else:
            raise ValueError(f"Unknown workflow: {workflow}")
    
    def _search_and_cite(self, context: AgentContext) -> Dict[str, Any]:
        query_result = self.query_agent.execute(context)
        context.intermediate_results["chunks"] = query_result["chunks"]
        
        citation_result = self.citation_agent.execute(context)
        
        return {
            "query": context.query,
            "workflow": "search_and_cite",
            "results": query_result,
            "citations": citation_result,
        }
    
    def _compare_and_cite(self, context: AgentContext) -> Dict[str, Any]:
        query_result = self.query_agent.execute(context)
        context.intermediate_results["chunks"] = query_result["chunks"]
        
        compare_result = self.compare_agent.execute(context)
        
        citation_result = self.citation_agent.execute(context)
        
        return {
            "query": context.query,
            "workflow": "compare_and_cite",
            "search_results": query_result,
            "comparison": compare_result,
            "citations": citation_result,
        }
    
    def _summarize_and_cite(self, context: AgentContext) -> Dict[str, Any]:
        query_result = self.query_agent.execute(context)
        context.intermediate_results["chunks"] = query_result["chunks"]
        
        summary_result = self.summarize_agent.execute(context)
        
        citation_result = self.citation_agent.execute(context)
        
        return {
            "query": context.query,
            "workflow": "summarize_and_cite",
            "search_results": query_result,
            "summary": summary_result,
            "citations": citation_result,
        }
    
    def custom_workflow(
        self,
        query: str,
        agents: List[Agent],
    ) -> Dict[str, Any]:
        context = AgentContext(
            query=query,
            intermediate_results={},
            active_documents=[],
            citations=[],
            screenshots=[],
        )
        
        results = {}
        
        for agent in agents:
            agent_result = agent.execute(context)
            results[agent.name] = agent_result
            
            if "chunks" in agent_result:
                context.intermediate_results["chunks"] = agent_result["chunks"]
        
        return {
            "query": query,
            "workflow": "custom",
            "results": results,
        }
