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


def test_build_guide_content_mentions_legacy_current_and_updates() -> None:
    from armarius.app import build_guide_content

    content = build_guide_content('zh-TW')

    assert content['legacy_title'] == '補充說明'
    assert any('單頁 Guide' in item for item in content['legacy_steps'])
    assert any('左側 Workflow' in item for item in content['current_steps'])
    assert content['updates_title'] == '為什麼現在這樣安排'
    assert any('單頁文件' in item or '單頁' in item for item in content['updates'])


def test_build_dashboard_overview_uses_queue_summary() -> None:
    from armarius.app import build_dashboard_overview

    overview = build_dashboard_overview(
        locale='zh-TW',
        queue_summary={
            'total_blobs': 5,
            'ingest': {'accepted': 2, 'quarantine': 1, 'needs_ocr': 1, 'rejected': 1},
            'processing': {'accepted_pending_normalize': 1, 'ready_for_analysis': 2, 'needs_ocr': 1, 'quarantined': 1, 'rejected': 1, 'normalized': 2},
            'stale': {'total': 1, 'accepted': 0, 'quarantine': 0, 'needs_ocr': 1, 'rejected': 0},
            'credibility': {'high': 2, 'medium': 1, 'low': 1, 'unknown': 1},
        },
        inbox_count=3,
        analyses_count=4,
        synthesis_count=1,
    )

    assert overview['headline_metrics'][0]['label'] == 'Blob 總數'
    assert overview['headline_metrics'][0]['value'] == '5'
    assert overview['queues'][0]['label'] == '收件匣待處理'
    assert overview['queues'][0]['count'] == '3'
    assert overview['credibility_summary']['items'][0]['count'] == '2'
    assert overview['next_actions'][0]['target'] == 'intake'


def test_dashboard_overview_prioritizes_navigation_over_execution() -> None:
    from armarius.app import build_dashboard_overview

    overview = build_dashboard_overview(
        locale='en-US',
        queue_summary={
            'total_blobs': 4,
            'ingest': {'accepted': 1, 'quarantine': 1, 'needs_ocr': 1, 'rejected': 1},
            'processing': {'accepted_pending_normalize': 1, 'ready_for_analysis': 1, 'needs_ocr': 1, 'quarantined': 1, 'rejected': 1, 'normalized': 1},
            'stale': {'total': 1, 'accepted': 0, 'quarantine': 0, 'needs_ocr': 1, 'rejected': 0},
            'credibility': {'high': 1, 'medium': 1, 'low': 1, 'unknown': 1},
        },
        inbox_count=2,
        analyses_count=0,
        synthesis_count=0,
    )

    assert all(item['target'] in {'statistics', 'intake', 'paradigm_analysis', 'concerto_synthesis'} for item in overview['queues'])
    assert overview['credibility_summary']['items'][1]['label'] == 'Medium'
    assert all(item['target'] in {'intake', 'paradigm_analysis'} for item in overview['next_actions'])


def test_build_sidebar_pages_is_simplified() -> None:
    from armarius.app import build_sidebar_pages

    pages = build_sidebar_pages('zh-TW')
    flat = [page_id for _, items in pages for page_id, _ in items]

    assert flat == ['dashboard', 'library', 'paradigm_analysis', 'concerto_synthesis', 'tutorial', 'catalog_assistant', 'settings']
