"""Tests for the onboarding home page content."""

from pathlib import Path

from armarius.app import get_onboarding_content


def test_get_onboarding_content_en_us() -> None:
    """Return English onboarding content with actionable steps."""
    content = get_onboarding_content("en-US", Path("/tmp/papers"))

    assert content["title"] == "Connect your PDF library to Armarius"
    assert len(content["steps"]) == 3
    assert content["steps"][0]["code"] == "uv tool install --editable '.[web]'"
    assert "armarius init --library-path /tmp/papers" == content["steps"][1]["code"]
    assert any("Library page" in tip for tip in content["tips"])


def test_get_onboarding_content_zh_tw() -> None:
    """Return Traditional Chinese onboarding content with localized labels."""
    content = get_onboarding_content("zh-TW", Path("/tmp/論文"))

    assert content["title"] == "把 PDF library 接上 Armarius"
    assert content["steps"][2]["title"] == "3. 開 Web"
    assert content["steps"][1]["code"] == "armarius init --library-path /tmp/論文"
    assert any("Library path:" in line for line in content["status_lines"])


def test_get_onboarding_content_mentions_workflow_outputs() -> None:
    """Keep dashboard helper text aligned with the Armarius workflow."""
    content = get_onboarding_content("en-US", Path("/tmp/papers"))

    assert any("Library page" in tip for tip in content["tips"])
    assert content["status_lines"][2] == "Config file: ~/.armarius/config.yaml"
