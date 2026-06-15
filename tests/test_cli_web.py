"""Tests for Armarius CLI web startup behavior."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from armarius.cli import _build_streamlit_command, main


class DummyConfig:
    """Minimal config object for CLI serve tests."""

    def __init__(self, config_path: Path, library_root: Path, web_port: int = 8501) -> None:
        """Store config-like values used by ``serve``.

        Args:
            config_path: Pretend config file path.
            library_root: Pretend library root path.
            web_port: Port exposed by the config.
        """
        self.config_path = config_path
        self.library_root = library_root
        self.web_port = web_port
        self.recursive_scan = True
        self.auto_open_browser = True

    def set(self, key_path: str, value: object) -> None:
        """Apply supported runtime overrides.

        Args:
            key_path: Dot-path key.
            value: Value to assign.
        """
        if key_path == "web.port":
            self.web_port = int(value)

    def get(self, key_path: str, default: object = None) -> object:
        """Return supported config values for CLI tests."""
        if key_path == "web.auto_open_browser":
            return self.auto_open_browser
        return default


@pytest.mark.parametrize(
    ("port", "expected_suffix"),
    [
        (8501, ["--server.port", "8501", "--server.address", "localhost"]),
        (9999, ["--server.port", "9999", "--server.address", "localhost"]),
    ],
)
def test_build_streamlit_command(port: int, expected_suffix: list[str]) -> None:
    """Build Streamlit command with deterministic web args."""
    command = _build_streamlit_command(port)

    assert command[:4] == [command[0], "-m", "streamlit", "run"]
    assert command[-4:] == expected_suffix
    assert command[4].endswith("armarius/app.py")


def test_serve_reports_missing_streamlit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Show actionable install hints when the web extra is absent."""
    runner = CliRunner()
    library_root = tmp_path / "papers"
    library_root.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text("web: {}\n", encoding="utf-8")

    monkeypatch.setattr("armarius.cli.importlib.util.find_spec", lambda name: None)
    monkeypatch.setattr("armarius.cli.ArmariusConfig", lambda: DummyConfig(config_path, library_root))

    result = runner.invoke(main, ["serve"])

    assert result.exit_code == 1
    assert "optional 'web' dependency" in result.output
    assert "uv tool install --editable '.[web]'" in result.output
    assert "pip install -e '.[web]'" in result.output


def test_serve_runs_streamlit_with_overridden_port(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Launch Streamlit through subprocess with the configured port."""
    runner = CliRunner()
    library_root = tmp_path / "papers"
    library_root.mkdir()
    config_path = tmp_path / "config.yaml"
    config_path.write_text("web: {}\n", encoding="utf-8")
    config = DummyConfig(config_path, library_root)

    mock_scanner = Mock()
    mock_scanner.scan.return_value = []
    mock_scanner.get_stats.return_value = {
        "total_count": 0,
        "readable_count": 0,
        "unreadable_count": 0,
        "total_size_mb": 0.0,
        "total_pages": 0,
    }

    captured: dict[str, object] = {}

    def fake_run(cmd: list[str], check: bool = False) -> Mock:
        captured["cmd"] = cmd
        captured["check"] = check
        return Mock(returncode=0)

    monkeypatch.setattr("armarius.cli.importlib.util.find_spec", lambda name: object())
    monkeypatch.setattr("armarius.cli.ArmariusConfig", lambda: config)
    monkeypatch.setattr("armarius.cli.PDFScanner", lambda *args, **kwargs: mock_scanner)
    monkeypatch.setattr("armarius.cli._open_web_ui", lambda url: None)
    monkeypatch.setattr("subprocess.run", fake_run)

    result = runner.invoke(main, ["serve", "--port", "8600"])

    assert result.exit_code == 0
    assert "http://localhost:8600" in result.output
    assert captured["check"] is False
    assert captured["cmd"][-4:] == ["--server.port", "8600", "--server.address", "localhost"]
