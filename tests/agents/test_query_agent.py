import pytest
from armarius.agents import QueryAgent, AgentContext
from armarius.storage import Embedder, VectorStore, SemanticSearch


@pytest.fixture
def query_agent(tmp_path):
    embedder = Embedder()
    vector_store = VectorStore(
        collection_name="test_query",
        data_dir=tmp_path / "qdrant",
        embedding_dim=embedder.dimension,
    )
    search = SemanticSearch(embedder, vector_store)
    return QueryAgent(search)


def test_query_agent_initialization(query_agent):
    assert query_agent.name == "QueryAgent"
    assert query_agent.search is not None


def test_query_agent_execute_empty(query_agent):
    context = AgentContext(
        query="test query",
        intermediate_results={},
        active_documents=[],
        citations=[],
        screenshots=[],
    )
    
    result = query_agent.execute(context)
    
    assert "chunks" in result
    assert "count" in result
    assert result["count"] == 0
