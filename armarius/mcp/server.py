"""MCP server for Armarius PDF knowledge management."""

import asyncio
from pathlib import Path
from typing import Any, Sequence
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import Field

from armarius.storage import DocumentIndexer, SemanticSearch, Embedder, VectorStore, SearchQuery
from armarius.agents import Orchestrator, QueryAgent, CompareAgent, SummarizeAgent, CitationAgent


app = Server("armarius-mcp")

embedder = Embedder()
vector_store = VectorStore(embedding_dim=embedder.dimension)
indexer = DocumentIndexer(embedder=embedder, vector_store=vector_store)
search = SemanticSearch(embedder=embedder, vector_store=vector_store)

query_agent = QueryAgent(search)
compare_agent = CompareAgent(vector_store)
summarize_agent = SummarizeAgent()
citation_agent = CitationAgent(screenshot_dir=Path.home() / ".armarius" / "screenshots")

orchestrator = Orchestrator(
    query_agent=query_agent,
    compare_agent=compare_agent,
    summarize_agent=summarize_agent,
    citation_agent=citation_agent,
)


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="index_pdf",
            description="Index a PDF file for semantic search",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "Path to PDF file to index",
                    },
                    "chunk_size": {
                        "type": "integer",
                        "description": "Chunk size for text splitting (default: 512)",
                        "default": 512,
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="search_pdfs",
            description="Semantic search across indexed PDFs",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="query_with_citations",
            description="Search and generate citations with bounding boxes",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to search for",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="compare_documents",
            description="Compare information across multiple documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic to compare across documents",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="summarize_documents",
            description="Synthesize information from multiple documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic to summarize",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    if name == "index_pdf":
        pdf_path = Path(arguments["pdf_path"])
        chunk_size = arguments.get("chunk_size", 512)
        
        count = indexer.index_pdf(pdf_path, chunk_size=chunk_size)
        
        return [
            TextContent(
                type="text",
                text=f"Indexed {count} chunks from {pdf_path.name}",
            )
        ]
    
    elif name == "search_pdfs":
        query = arguments["query"]
        top_k = arguments.get("top_k", 10)
        
        search_query = SearchQuery(text=query, top_k=top_k)
        results = search.search(search_query)
        
        output = f"Found {len(results)} results:\n\n"
        for i, result in enumerate(results, 1):
            output += f"{i}. [{Path(result.chunk.pdf_path).name}, page {result.chunk.bbox.page}]\n"
            output += f"   Score: {result.score:.3f}\n"
            output += f"   {result.chunk.text[:200]}...\n\n"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "query_with_citations":
        query = arguments["query"]
        result = orchestrator.process_query(query, workflow="search_and_cite")
        
        output = f"Query: {query}\n\n"
        output += f"Found {result['results']['count']} results\n\n"
        
        for i, citation in enumerate(result['citations']['citations'][:5], 1):
            output += f"{i}. {citation['title'] or Path(citation['pdf_path']).name}\n"
            output += f"   Page {citation['page']}, bbox: {citation['bbox']}\n"
            output += f"   {citation['text'][:150]}...\n\n"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "compare_documents":
        query = arguments["query"]
        result = orchestrator.process_query(query, workflow="compare_and_cite")
        
        comparison = result['comparison']['comparison']
        output = f"Comparison for: {query}\n\n"
        output += f"PDFs involved: {len(comparison['pdfs_involved'])}\n"
        output += f"Cross-document pairs found: {comparison['cross_document_pairs']}\n\n"
        
        return [TextContent(type="text", text=output)]
    
    elif name == "summarize_documents":
        query = arguments["query"]
        result = orchestrator.process_query(query, workflow="summarize_and_cite")
        
        summary = result['summary']['summary']
        output = f"Summary for: {query}\n\n{summary}\n"
        
        return [TextContent(type="text", text=output)]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def _serve():
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def main():
    """Console-script entrypoint: run the MCP stdio server."""
    asyncio.run(_serve())


if __name__ == "__main__":
    main()
