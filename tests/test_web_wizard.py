from pathlib import Path

from armarius.app import build_home_wizard_state, run_home_wizard_action


class DummyConfig:
    def __init__(self, library_root: Path) -> None:
        self.library_root = library_root
        self.saved = False

    def set(self, key: str, value: object) -> None:
        if key == "library.root_path":
            self.library_root = Path(str(value))

    def save(self) -> None:
        self.saved = True


class DummyRecord:
    def __init__(self, blob_id: str, state: str) -> None:
        self.document_blob_id = blob_id
        self.ingest_state = state


class DummyIntakeService:
    def __init__(self, results: list[DummyRecord] | None = None) -> None:
        self.results = results or []
        self.normalized: list[str] = []

    def intake_inbox(self) -> list[DummyRecord]:
        return self.results

    def normalize_blob(self, blob_id: str) -> None:
        self.normalized.append(blob_id)


def test_build_home_wizard_state_with_missing_library() -> None:
    payload = build_home_wizard_state(Path('/tmp/missing-library-for-armarius-test'))

    assert payload['steps'][0]['status'] == 'done'
    assert payload['steps'][1]['status'] == 'pending'
    assert payload['steps'][2]['status'] == 'blocked'
    assert payload['steps'][3]['status'] == 'blocked'


def test_build_home_wizard_state_with_existing_library(tmp_path: Path) -> None:
    library_root = tmp_path / 'papers'
    library_root.mkdir()
    (library_root / '_inbox').mkdir()
    (library_root / '_inbox' / 'paper.pdf').write_bytes(b'%PDF-1.4')

    payload = build_home_wizard_state(library_root)

    assert payload['steps'][1]['status'] == 'done'
    assert payload['steps'][2]['status'] == 'ready'
    assert payload['steps'][2]['detail'] == '1 PDFs waiting in inbox.'
    assert payload['steps'][3]['status'] == 'ready'


def test_run_home_wizard_action_updates_library_path(tmp_path: Path) -> None:
    target = tmp_path / 'papers'
    config = DummyConfig(target)

    result = run_home_wizard_action('library', config, intake_service=None, library_root=target)

    assert config.saved is True
    assert result['outcome'] == 'success'
    assert 'Library path saved' in result['message']


def test_run_home_wizard_action_processes_inbox() -> None:
    config = DummyConfig(Path('/tmp/papers'))
    intake = DummyIntakeService([DummyRecord('a', 'accepted'), DummyRecord('b', 'quarantine')])

    result = run_home_wizard_action('inbox', config, intake_service=intake, library_root=Path('/tmp/papers'))

    assert result['outcome'] == 'success'
    assert intake.normalized == ['a']
    assert 'Processed 2 files' in result['message']


def test_run_home_wizard_action_routes_review() -> None:
    config = DummyConfig(Path('/tmp/papers'))

    result = run_home_wizard_action('review', config, intake_service=None, library_root=Path('/tmp/papers'))

    assert result['outcome'] == 'navigate'
    assert result['page'] == 'library'
    assert result['room'] == 'intake'


def test_sidebar_workflow_steps_reflect_existing_library(tmp_path: Path) -> None:
    from armarius.app import build_sidebar_workflow_steps

    library_root = tmp_path / 'papers'
    library_root.mkdir()
    (library_root / '_inbox').mkdir()
    (library_root / '_inbox' / 'paper.pdf').write_bytes(b'%PDF-1.4')

    payload = build_sidebar_workflow_steps(library_root, current_page='dashboard', current_room='')

    assert [step['page'] for step in payload] == ['dashboard', 'library', 'library', 'library', 'paradigm_analysis', 'concerto_synthesis']
    assert payload[1]['room'] == 'statistics'
    assert payload[2]['room'] == 'intake'
    assert payload[2]['status'] == 'ready'


def test_sidebar_navigation_marks_current_and_next(tmp_path: Path) -> None:
    from armarius.app import build_sidebar_workflow_steps

    library_root = tmp_path / 'papers'
    library_root.mkdir()

    steps = build_sidebar_workflow_steps(library_root, current_page='dashboard', current_room='')

    assert steps[0]['is_current'] is True
    assert steps[1]['is_next'] is True
    assert 'Library folder exists' in steps[1]['summary']


def test_sidebar_navigation_sets_intake_current(tmp_path: Path) -> None:
    from armarius.app import build_sidebar_workflow_steps

    library_root = tmp_path / 'papers'
    library_root.mkdir()
    (library_root / '_inbox').mkdir()
    (library_root / '_inbox' / 'paper.pdf').write_bytes(b'%PDF-1.4')

    steps = build_sidebar_workflow_steps(library_root, current_page='library', current_room='intake')

    intake_step = next(step for step in steps if step['title'] == '3. Process inbox')
    review_step = next(step for step in steps if step['title'] == '4. Review intake')
    assert intake_step['is_current'] is True
    assert review_step['is_next'] is True


def test_sidebar_workflow_includes_settings_page_target(tmp_path: Path) -> None:
    from armarius.app import build_sidebar_pages

    pages = build_sidebar_pages('zh-TW')

    assert any(page_id == 'settings' for _, items in pages for page_id, _ in items)
