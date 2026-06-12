"""CLI interface for Cardex.

Provides commands: init, serve, scan
"""

import sys
from pathlib import Path

import click

from armarius.config import CardexConfig
from armarius.scanner import PDFScanner


@click.group()
@click.version_option(version="0.2.0", prog_name="cardex")
def main():
    """Cardex - Academic Knowledge Management System.

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
    """Initialize Cardex configuration.

    Creates ~/.cardex/config.yaml with your settings.
    """
    click.echo("📂 Cardex Initialization")
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
    config = CardexConfig()
    config.set("library.root_path", str(library_path))
    config.set("web.port", port)
    config.set("web.auto_open_browser", not no_browser)
    config.save()

    click.echo()
    click.echo(f"✅ Configuration saved to {config.config_path}")
    click.echo(f"✅ Log directory: {CardexConfig.DEFAULT_LOG_DIR}")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  1. Place PDFs in {library_path}")
    click.echo("  2. Run 'cardex serve' to start the web UI")


@main.command()
@click.option(
    "--port",
    type=int,
    help="Override web UI port from config",
)
def serve(port: int):
    """Start the Cardex web UI.

    Opens Streamlit interface to browse your PDF library.
    """
    config = CardexConfig()

    # Check if config exists
    if not config.config_path.exists():
        click.echo("❌ Config not found. Run 'cardex init' first.", err=True)
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
    try:
        pdf_list = scanner.scan()
        stats = scanner.get_stats(pdf_list)

        click.echo()
        click.echo("🚀 Cardex is starting!")
        click.echo(f"   Web UI: http://localhost:{config.web_port}")
        click.echo(f"   Library: {library_root}")
        click.echo(f"   PDFs found: {stats['total_count']} files")
        click.echo()
        click.echo("   Press Ctrl+C to stop")
        click.echo()

    except Exception as e:
        click.echo(f"⚠️  Warning: {e}", err=True)

    # Launch Streamlit
    import subprocess

    app_path = Path(__file__).parent / "app.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port",
        str(config.web_port),
        "--server.headless",
        "true",
    ]

    if not config.get("web.auto_open_browser", True):
        cmd.extend(["--server.headless", "true"])

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        click.echo("\n👋 Cardex stopped.")


@main.command()
def scan():
    """Scan library and display PDF statistics.

    Quick way to see what PDFs are in your library without starting the web UI.
    """
    config = CardexConfig()

    if not config.config_path.exists():
        click.echo("❌ Config not found. Run 'cardex init' first.", err=True)
        sys.exit(1)

    library_root = config.library_root

    if not library_root.exists():
        click.echo(f"❌ Library path not found: {library_root}", err=True)
        sys.exit(1)

    click.echo(f"🔍 Scanning: {library_root}")
    click.echo()

    scanner = PDFScanner(library_root, recursive=config.recursive_scan)
    pdf_list = scanner.scan()
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


if __name__ == "__main__":
    main()
