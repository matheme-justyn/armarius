import pytest
from armarius.agents import AgentContext, Citation


def test_agent_context_creation():
    context = AgentContext(
        query="test query",
        intermediate_results={},
        active_documents=[],
        citations=[],
        screenshots=[],
    )
    
    assert context.query == "test query"
    assert context.intermediate_results == {}
    assert context.active_documents == []


def test_citation_creation():
    citation = Citation(
        text="Sample text",
        pdf_path="/test/doc.pdf",
        page=1,
        bbox={"x0": 100, "y0": 200, "x1": 300, "y1": 250},
    )
    
    assert citation.text == "Sample text"
    assert citation.pdf_path == "/test/doc.pdf"
    assert citation.page == 1
    assert citation.bbox["x0"] == 100


def test_citation_to_dict():
    citation = Citation(
        text="Sample text",
        pdf_path="/test/doc.pdf",
        page=1,
        bbox={"x0": 100, "y0": 200, "x1": 300, "y1": 250},
        title="Test Document",
        authors="John Doe",
    )
    
    result = citation.to_dict()
    
    assert result["text"] == "Sample text"
    assert result["pdf_path"] == "/test/doc.pdf"
    assert result["page"] == 1
    assert result["title"] == "Test Document"
    assert result["authors"] == "John Doe"
