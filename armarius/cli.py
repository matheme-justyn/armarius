"""CLI interface for Armarius.

Provides commands: init, serve, scan, intake.
"""

import importlib.util
import sys
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

import click

from armarius.config import ArmariusConfig
from armarius.scanner import PDFScanner
from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor
from armarius.review_draft import ReviewDraftService



def _build_database(config: ArmariusConfig) -> ArmariusDatabase:
    """Create a database handle using the configured database path."""
    return ArmariusDatabase(db_path=Path(str(config.get("database.path"))))


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


@main.group()
def intake():
    """Intake-related commands."""
    pass


@intake.command("run")
@click.argument("files", nargs=-1, type=click.Path(exists=True, path_type=Path))
def intake_run(files: tuple[Path, ...]):
    """Validate and register inbound files through the intake pipeline."""
    if not files:
        click.echo("❌ No files provided.", err=True)
        raise SystemExit(1)

    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)

    for file_path in files:
        record = service.intake_file(file_path)
        status_emoji = "✅" if record.ingest_state == "accepted" else "❌"
        reason = "" if not record.reason else f" ({record.reason})"
        click.echo(f"{status_emoji} {file_path.name} -> {record.managed_path}{reason}")


@intake.command("scan-inbox")
@click.option("--normalize", "normalize_after", is_flag=True, help="Normalize accepted blobs immediately")
def intake_scan_inbox(normalize_after: bool):
    """Process every file currently found in the inbox."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    results = service.intake_inbox()
    if not results:
        click.echo("ℹ️ Inbox is empty.")
        return
    for record in results:
        status_emoji = "✅" if record.ingest_state == "accepted" else "❌"
        reason = "" if not record.reason else f" ({record.reason})"
        click.echo(f"{status_emoji} {record.managed_path.name} [{record.ingest_state}]{reason}")
        if normalize_after and record.ingest_state == "accepted":
            artifacts = service.normalize_blob(record.document_blob_id)
            click.echo(f"   ↳ normalized -> {artifacts.markdown_path}")


@main.group()
def normalize():
    """Normalization-related commands."""
    pass


@normalize.command("run")
@click.argument("blob_id")
def normalize_run(blob_id: str):
    """Generate normalized artifacts for one accepted blob."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    artifacts = service.normalize_blob(blob_id)
    click.echo(f"✅ Markdown: {artifacts.markdown_path}")
    click.echo(f"✅ Raw text: {artifacts.raw_text_path}")
    click.echo(f"✅ Manifest: {artifacts.manifest_path}")


@main.group()
def trace():
    """Trace and provenance commands."""
    pass


@trace.command("show")
@click.argument("blob_id")
@click.option("--json-output", is_flag=True, help="Render trace as JSON")
def trace_show(blob_id: str, json_output: bool):
    """Display provenance information for one blob."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    payload = service.trace_blob(blob_id)
    if json_output:
        import json
        click.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    click.echo(f"Blob: {payload['blob_id']}")
    click.echo(f"State: {payload['ingest_state']}")
    click.echo(f"Managed path: {payload['managed_path']}")
    click.echo(f"Blob SHA256: {payload['blob_sha256']}")
    click.echo(f"Text SHA256: {payload['text_sha256']}")
    if payload['root']:
        click.echo(f"Canonical DOI: {payload['root']['canonical_doi']}")
        click.echo(f"Canonical title: {payload['root']['canonical_title']}")
    if payload['artifacts']:
        click.echo("Artifacts:")
        for artifact in payload['artifacts']:
            click.echo(f"- {artifact['artifact_type']}: {artifact['path']}")


@main.group()
def rename():
    """Managed rename commands."""
    pass


@rename.command("propose")
@click.argument("blob_id")
def rename_propose(blob_id: str):
    """Show the proposed canonical filename for one blob."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    proposal = service.propose_filename(blob_id)
    click.echo(f"Blob: {proposal['blob_id']}")
    click.echo(f"Strategy: {proposal['strategy']}")
    click.echo(f"Proposed filename: {proposal['proposed_filename']}")


@rename.command("apply")
@click.argument("blob_id")
def rename_apply(blob_id: str):
    """Apply the proposed canonical filename for one blob."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    result = service.apply_filename(blob_id)
    click.echo(f"✅ Renamed using {result['strategy']}")
    click.echo(f"Old path: {result['old_path']}")
    click.echo(f"New path: {result['new_path']}")


@trace.command("list")
@click.option("--state", "states", multiple=True, help="Filter by ingest state")
@click.option("--limit", default=20, help="Maximum blobs to list")
def trace_list(states: tuple[str, ...], limit: int):
    """List recent blobs for intake review."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    rows = service.list_recent_blobs(limit=limit, states=list(states) if states else None)
    for row in rows:
        click.echo(f"{row['id']}	{row['ingest_state']}	{row['managed_filename']}")


@main.group()
def review():
    """Review and triage commands for intake blobs."""
    pass


@review.command("set-state")
@click.argument("blob_id")
@click.argument("new_state")
def review_set_state(blob_id: str, new_state: str):
    """Move one blob to a new intake state."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    result = service.update_ingest_state(blob_id, new_state)
    click.echo(f"✅ {blob_id} -> {result['new_state']}")
    click.echo(f"New path: {result['new_path']}")


@review.command("retry-normalize")
@click.argument("blob_id")
def review_retry_normalize(blob_id: str):
    """Retry normalization for one blob."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    artifacts = service.normalize_blob(blob_id)
    click.echo(f"✅ Markdown: {artifacts.markdown_path}")


@review.command("apply-rename")
@click.argument("blob_id")
def review_apply_rename(blob_id: str):
    """Apply the canonical rename proposal for one blob."""
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    result = service.apply_filename(blob_id)
    click.echo(f"✅ Renamed -> {result['new_path']}")


@review.command("batch-retry-normalize")
@click.argument("blob_ids", nargs=-1)
def review_batch_retry_normalize(blob_ids: tuple[str, ...]):
    """Retry normalization for multiple blobs."""
    if not blob_ids:
        click.echo("❌ No blob ids provided.", err=True)
        raise SystemExit(1)
    config = ArmariusConfig()
    service = IntakeService(_build_database(config), PDFProcessor(), config.library_root)
    artifacts = service.batch_normalize(list(blob_ids))
    click.echo(f"✅ Normalized {len(artifacts)} blobs")


@main.command("review-draft")
@click.argument("paradigm_id")
@click.option("--concerto", default="literature_review", help="Draft framing name")
@click.option("--persona", "personas", multiple=True, help="Add an explicit perspective section")
def review_draft(paradigm_id: str, concerto: str, personas: tuple[str, ...]):
    """Generate a minimal literature-review draft from saved analyses."""
    config = ArmariusConfig()
    service = ReviewDraftService(_build_database(config), config.library_root)
    result = service.generate(paradigm_id=paradigm_id, concerto=concerto, personas=list(personas))
    click.echo(f"✅ Draft: {result['output_path']}")
    click.echo(f"Analyses: {len(result['analysis_ids'])}")
    if result['personas']:
        click.echo(f"Perspectives: {', '.join(result['personas'])}")
