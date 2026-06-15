"""Tests for the Armarius CLI."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from armarius.cli import main
from armarius.config import ArmariusConfig


@pytest.fixture()
def cli_runner() -> CliRunner:
    """Create a Click CLI runner."""
    return CliRunner()


@pytest.fixture()
def temp_config_path(tmp_path: Path) -> Path:
    """Create a temporary config path for CLI tests."""
    return tmp_path / "config.yaml"


def test_init_keeps_browser_auto_open_enabled_by_default(
    cli_runner: CliRunner,
    temp_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The init command should keep browser auto-open enabled by default."""
    library_path = tmp_path / "library"
    library_path.mkdir()

    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_PATH", temp_config_path)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_DIR", temp_config_path.parent)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_LOG_DIR", temp_config_path.parent / "logs")

    result = cli_runner.invoke(main, ["init", "--library-path", str(library_path)])

    assert result.exit_code == 0
    saved_text = temp_config_path.read_text(encoding="utf-8")
    assert "auto_open_browser: true" in saved_text


def test_init_can_disable_browser_auto_open(
    cli_runner: CliRunner,
    temp_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The init command should still allow disabling browser auto-open."""
    library_path = tmp_path / "library"
    library_path.mkdir()

    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_PATH", temp_config_path)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_DIR", temp_config_path.parent)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_LOG_DIR", temp_config_path.parent / "logs")

    result = cli_runner.invoke(
        main,
        ["init", "--library-path", str(library_path), "--no-browser"],
    )

    assert result.exit_code == 0
    saved_text = temp_config_path.read_text(encoding="utf-8")
    assert "auto_open_browser: false" in saved_text


def test_serve_opens_browser_when_enabled(
    cli_runner: CliRunner,
    temp_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The serve command should open the browser when auto-open is enabled."""
    library_path = tmp_path / "library"
    library_path.mkdir()
    temp_config_path.write_text(
        "\n".join(
            [
                "library:",
                f"  root_path: {library_path}",
                "  recursive_scan: true",
                "web:",
                "  host: localhost",
                "  port: 8765",
                "  auto_open_browser: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_PATH", temp_config_path)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_DIR", temp_config_path.parent)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_LOG_DIR", temp_config_path.parent / "logs")
    monkeypatch.setattr("armarius.cli.importlib.util.find_spec", lambda name: object())

    opened_urls: list[str] = []
    monkeypatch.setattr("armarius.cli._open_web_ui", lambda url: opened_urls.append(url))

    class DummyScanner:
        """Minimal scanner stub for serve tests."""

        def __init__(self, library_root: Path, recursive: bool) -> None:
            self.library_root = library_root
            self.recursive = recursive

        def scan(self) -> list[object]:
            """Return an empty PDF list."""
            return []

        def get_stats(self, pdf_list: list[object]) -> dict[str, int]:
            """Return minimal scan statistics."""
            return {"total_count": 0}

    monkeypatch.setattr("armarius.cli.PDFScanner", DummyScanner)

    class DummyCompletedProcess:
        """Subprocess result stub."""

        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    monkeypatch.setattr(
        "subprocess.run",
        lambda cmd, check=False: DummyCompletedProcess(0),
    )

    result = cli_runner.invoke(main, ["serve"])

    assert result.exit_code == 0
    assert opened_urls == ["http://localhost:8765"]


def test_scan_shows_progress_for_each_pdf(
    cli_runner: CliRunner,
    temp_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The scan command should show progress while inspecting PDFs."""
    library_path = tmp_path / "library"
    library_path.mkdir()
    temp_config_path.write_text(
        "\n".join(
            [
                "library:",
                f"  root_path: {library_path}",
                "  recursive_scan: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_PATH", temp_config_path)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_CONFIG_DIR", temp_config_path.parent)
    monkeypatch.setattr(ArmariusConfig, "DEFAULT_LOG_DIR", temp_config_path.parent / "logs")

    class DummyScanner:
        """Minimal scanner stub for scan progress tests."""

        def __init__(self, root_path: Path, recursive: bool = True) -> None:
            self.root_path = root_path
            self.recursive = recursive

        def scan(self, progress_callback=None) -> list[object]:
            """Trigger progress updates for two fake PDFs."""
            first = self.root_path / "paper-1.pdf"
            second = self.root_path / "paper-2.pdf"
            if progress_callback is not None:
                progress_callback(1, 2, first)
                progress_callback(2, 2, second)
            return []

        def get_stats(self, pdf_list: list[object]) -> dict[str, int | float]:
            """Return minimal scan stats."""
            return {
                "total_count": 0,
                "readable_count": 0,
                "unreadable_count": 0,
                "total_size_mb": 0.0,
                "total_pages": 0,
            }

    monkeypatch.setattr("armarius.cli.PDFScanner", DummyScanner)

    result = cli_runner.invoke(main, ["scan"])

    assert result.exit_code == 0
    assert "Discovering and validating PDF files" in result.output
    assert "[1/2] Checking paper-1.pdf..." in result.output
    assert "[2/2] Checking paper-2.pdf..." in result.output
