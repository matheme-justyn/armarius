"""CLI interface for Armarius.

Provides commands: init, serve, scan.
"""

import importlib.util
import sys
import webbrowser
from pathlib import Path

import click

from armarius.config import ArmariusConfig
from armarius.scanner import PDFScanner


def _build_streamlit_command(port: int) -> list[str]:
    """Build the Streamlit launch command for the web UI.

    Args:
        port: Port for the Streamlit server.

    Returns:
        Command arguments for ``subprocess.run``.
    """
    app_path = Path(__file__).parent / "app.py"
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(port),
        "--server.address",
        "localhost",
    ]


def _open_web_ui(url: str) -> None:
    """Open the web UI in the user's default browser.

    Args:
        url: The URL to open.
    """
    webbrowser.open(url)


def _echo_scan_progress(current: int, total: int, pdf_path: Path) -> None:
    """Show scan progress for long-running PDF inspection.

    Args:
        current: Current file index, starting at 1.
        total: Total number of PDF files discovered.
        pdf_path: Path of the PDF currently being inspected.
    """
    click.echo(f"   [{current}/{total}] Checking {pdf_path.name}...", err=True)


@click.group()
@click.version_option(version="0.7.1", prog_name="armarius")
def main():
    """Armarius - Academic Knowledge Management System.

    Transform your PDF collection into a queryable knowledge base.
    """
    pass


@main.command()
@click.option(
    "--library-path",
    type=click.Path(),
    help="Path to your PDF library folder",
)
@click.option(
    "--port",
    type=int,
    default=8501,
    help="Web UI port (default: 8501)",
)
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't auto-open browser",
)
def init(library_path: str, port: int, no_browser: bool):
    """Initialize Armarius configuration.

    Creates ~/.armarius/config.yaml with your settings.
    """
    click.echo("📂 Armarius Initialization")
    click.echo("=" * 40)
    click.echo()

    # Prompt for library path if not provided
    if not library_path:
        default_path = str(Path.home() / "Documents" / "papers")
        library_path = click.prompt(
            "Library root path",
            default=default_path,
            type=click.Path(),
        )

    library_path = Path(library_path).expanduser().resolve()

    # Check if path exists
    if not library_path.exists():
        if click.confirm(f"Directory {library_path} does not exist. Create it?"):
            library_path.mkdir(parents=True, exist_ok=True)
            click.echo(f"✅ Created directory: {library_path}")
        else:
            click.echo("❌ Initialization cancelled.")
            sys.exit(1)

    # Create config
    config = ArmariusConfig()
    config.set("library.root_path", str(library_path))
    config.set("web.port", port)
    config.set("web.auto_open_browser", not no_browser)
    config.save()

    click.echo()
    click.echo(f"✅ Configuration saved to {config.config_path}")
    click.echo(f"✅ Log directory: {ArmariusConfig.DEFAULT_LOG_DIR}")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  1. Place PDFs in {library_path}")
    click.echo("  2. Run 'armarius serve' to start the web UI")


@main.command()
@click.option(
    "--port",
    type=int,
    help="Override web UI port from config",
)
def serve(port: int):
    """Start the Armarius web UI.

    Opens Streamlit interface to browse your PDF library.
    """
    if importlib.util.find_spec("streamlit") is None:
        click.echo(
            "❌ streamlit is not installed (it is an optional 'web' dependency).",
            err=True,
        )
        click.echo("   Install with one of these commands:", err=True)
        click.echo("   - uv tool install --editable '.[web]'", err=True)
        click.echo("   - pip install -e '.[web]'", err=True)
        sys.exit(1)

    config = ArmariusConfig()

    # Check if config exists
    if not config.config_path.exists():
        click.echo("❌ Config not found. Run 'armarius init' first.", err=True)
        sys.exit(1)

    # Check if library path exists
    library_root = config.library_root
    if not library_root.exists():
        click.echo(f"❌ Library path not found: {library_root}", err=True)
        click.echo("   Update path in config or create the directory.", err=True)
        sys.exit(1)

    # Override port if provided
    if port:
        config.set("web.port", port)

    # Quick scan to show stats
    click.echo("🔍 Scanning library...")
    scanner = PDFScanner(library_root, recursive=config.recursive_scan)
    web_url = f"http://localhost:{config.web_port}"

    try:
        pdf_list = scanner.scan()
        stats = scanner.get_stats(pdf_list)

        click.echo()
        click.echo("🚀 Armarius is starting!")
        click.echo(f"   Web UI: {web_url}")
        click.echo(f"   Library: {library_root}")
        click.echo(f"   PDFs found: {stats['total_count']} files")
        click.echo()
        click.echo("   Press Ctrl+C to stop")
        click.echo()

    except Exception as e:
        click.echo(f"⚠️  Warning: {e}", err=True)

    import subprocess
    cmd = _build_streamlit_command(config.web_port)

    if config.get("web.auto_open_browser", True):
        try:
            _open_web_ui(web_url)
        except Exception as exc:
            click.echo(f"⚠️  Could not open browser automatically: {exc}", err=True)

    try:
        raise SystemExit(subprocess.run(cmd, check=False).returncode)
    except KeyboardInterrupt:
        click.echo("\n👋 Armarius stopped.")


@main.command()
def scan():
    """Scan library and display PDF statistics.

    Quick way to see what PDFs are in your library without starting the web UI.
    """
    config = ArmariusConfig()

    if not config.config_path.exists():
        click.echo("❌ Config not found. Run 'armarius init' first.", err=True)
        sys.exit(1)

    library_root = config.library_root

    if not library_root.exists():
        click.echo(f"❌ Library path not found: {library_root}", err=True)
        sys.exit(1)

    click.echo(f"🔍 Scanning: {library_root}")
    click.echo()

    scanner = PDFScanner(library_root, recursive=config.recursive_scan)
    click.echo("⏳ Discovering and validating PDF files...")
    pdf_list = scanner.scan(progress_callback=_echo_scan_progress)
    stats = scanner.get_stats(pdf_list)

    # Display statistics
    click.echo("📊 Statistics:")
    click.echo(f"   Total PDFs: {stats['total_count']}")
    click.echo(f"   Readable: {stats['readable_count']}")
    click.echo(f"   Unreadable: {stats['unreadable_count']}")
    click.echo(f"   Total size: {stats['total_size_mb']:.2f} MB")
    if stats["total_pages"]:
        click.echo(f"   Total pages: {stats['total_pages']}")
    click.echo()

    # Show first 10 files
    if pdf_list:
        click.echo("📄 Sample files (first 10):")
        for pdf in pdf_list[:10]:
            status = "✅" if pdf.is_readable else "❌"
            click.echo(f"   {status} {pdf.filename} ({pdf.size_mb:.2f} MB)")

        if len(pdf_list) > 10:
            click.echo(f"   ... and {len(pdf_list) - 10} more")


# ---------------------------------------------------------------------------
# Semantic search & multi-agent commands (merged from Capsa)
#
# Heavy dependencies (sentence-transformers, qdrant-client) are imported lazily
# inside each command so `armarius --help` and the lightweight commands above
# stay fast.
# ---------------------------------------------------------------------------


@main.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--chunk-size", default=512, help="Chunk size for text splitting")
@click.option(
    "--strategy",
    type=click.Choice(["block", "sentence", "fixed"]),
    default="block",
    help="Chunking strategy",
)
def index(path: str, chunk_size: int, strategy: str):
    """Index PDF files for semantic search."""
    from rich.console import Console

    from armarius.storage import DocumentIndexer, Embedder, VectorStore
    from armarius.parser import ChunkingStrategy

    console = Console()
    path = Path(path)

    embedder = Embedder()
    vector_store = VectorStore(embedding_dim=embedder.dimension)

    strategy_map = {
        "block": ChunkingStrategy.BLOCK,
        "sentence": ChunkingStrategy.SENTENCE,
        "fixed": ChunkingStrategy.FIXED,
    }

    indexer = DocumentIndexer(
        embedder=embedder,
        vector_store=vector_store,
        chunking_strategy=strategy_map[strategy],
    )

    with console.status(f"[bold green]Indexing {path}..."):
        if path.is_file():
            count = indexer.index_pdf(path, chunk_size=chunk_size)
            console.print(f"✓ Indexed {count} chunks from {path.name}", style="bold green")
        else:
            results = indexer.index_directory(path, chunk_size=chunk_size)
            total = sum(c for c in results.values() if c > 0)
            console.print(
                f"✓ Indexed {total} chunks from {len(results)} PDFs", style="bold green"
            )


@main.command()
@click.argument("query_text")
@click.option("--top-k", default=10, help="Number of results to return")
@click.option("--pdf", help="Search within a specific PDF")
def query(query_text: str, top_k: int, pdf: str):
    """Search across indexed PDFs with semantic search."""
    from rich.console import Console
    from rich.table import Table

    from armarius.storage import Embedder, VectorStore, SemanticSearch, SearchQuery

    console = Console()

    embedder = Embedder()
    vector_store = VectorStore(embedding_dim=embedder.dimension)
    search = SemanticSearch(embedder=embedder, vector_store=vector_store)

    search_query = SearchQuery(text=query_text, top_k=top_k, pdf_path=pdf)

    with console.status(f"[bold blue]Searching for: {query_text}..."):
        results = search.search(search_query)

    if not results:
        console.print("No results found", style="yellow")
        return

    table = Table(title=f"Search Results ({len(results)} found)")
    table.add_column("Rank", style="cyan")
    table.add_column("PDF", style="magenta")
    table.add_column("Page", style="green")
    table.add_column("Score", style="yellow")
    table.add_column("Text Preview", style="white")

    for i, result in enumerate(results, 1):
        pdf_name = Path(result.chunk.pdf_path).name
        page = str(result.chunk.bbox.page)
        score = f"{result.score:.3f}"
        text = result.chunk.text[:100] + "..."
        table.add_row(str(i), pdf_name, page, score, text)

    console.print(table)


@main.command(name="index-status")
def index_status():
    """Show semantic index status (vector store statistics)."""
    from rich.console import Console

    from armarius.storage import Embedder, VectorStore

    console = Console()

    embedder = Embedder()
    vector_store = VectorStore(embedding_dim=embedder.dimension)

    count = vector_store.count()

    console.print(f"Total indexed chunks: {count}", style="bold cyan")
    console.print(f"Embedding model: {embedder.config.model_name}", style="dim")
    console.print(f"Vector dimension: {embedder.dimension}", style="dim")


if __name__ == "__main__":
    main()
