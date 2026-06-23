"""Streamlit web UI for Armarius Phase 0.

Browse and search PDF library with i18n and theme support.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import streamlit as st
import toml

from armarius.config import ArmariusConfig
from armarius.scanner import PDFScanner
from armarius.workflow import LibraryWorkflow, LibraryStatus
from armarius.database import ArmariusDatabase
from armarius.intake_service import IntakeService
from armarius.pdf_processing import PDFProcessor
from armarius.ui_common import I18n, apply_theme, render_sidebar_settings
from armarius.catalog_assistant import render_catalog_assistant
from armarius.catalog_room import render_catalog_room


WORKFLOW_GUIDE_PATH = Path(__file__).resolve().parent.parent / "docs" / "workflow-guide.md"


def format_file_size(size_bytes: int | None) -> str:
    """Format bytes into a human-readable size string."""
    if size_bytes is None:
        return "N/A"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def load_workflow_guide_markdown() -> str:
    """Load the standalone workflow guide markdown.

    Returns:
        Workflow guide markdown content, or a fallback message if unavailable.
    """
    try:
        return WORKFLOW_GUIDE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "# Workflow Guide\n\nWorkflow guide file not found."


def get_onboarding_content(locale: str, library_root: Path) -> dict[str, object]:
    """Return onboarding copy for the home page.

    Args:
        locale: Active locale code.
        library_root: Configured PDF library path.

    Returns:
        Dictionary with localized onboarding content.
    """
    if locale == "zh-TW":
        return {
            "badge": "第一次打開 Armarius？先照這三步。",
            "title": "把 PDF library 接上 Armarius",
            "intro": "Armarius 已經可以用本機 checkout 安裝、初始化設定，並用 Web UI 檢視你的文獻庫。這個首頁先帶你完成最短上手路徑。",
            "steps": [
                {
                    "title": "1. 安裝",
                    "body": "建議直接把目前 repo 安裝成可執行工具。",
                    "code": "uv tool install --editable '.[web]'",
                },
                {
                    "title": "2. 初始化",
                    "body": "設定你的 PDF 文獻資料夾，Armarius 會建立 `~/.armarius/config.yaml`。",
                    "code": f"armarius init --library-path {library_root}",
                },
                {
                    "title": "3. 開 Web",
                    "body": "啟動本地 Web UI，直接在瀏覽器查看 library 狀態。",
                    "code": "armarius serve",
                },
            ],
            "tips_title": "你接下來可以做什麼",
            "tips": [
                "把 PDF 放進目前設定的 library folder。",
                "切到 Library 分頁看掃描結果與基本統計。",
                "切到 Tutorial 看目前功能與下一步。",
                "如果畫面是空的，先確認資料夾裡真的有 `.pdf`。",
            ],
            "status_title": "目前設定",
            "status_lines": [
                f"Library path: {library_root}",
                "Web UI: http://localhost:8501",
                "Config file: ~/.armarius/config.yaml",
            ],
        }

    return {
        "badge": "First time opening Armarius? Start here.",
        "title": "Connect your PDF library to Armarius",
        "intro": "Armarius can already be installed from a local checkout, initialized once, and opened in a local web UI. This home page gives you the shortest path to a working setup.",
        "steps": [
            {
                "title": "1. Install",
                "body": "Install the current checkout as a runnable local tool.",
                "code": "uv tool install --editable '.[web]'",
            },
            {
                "title": "2. Initialize",
                "body": "Point Armarius at your PDF library and create `~/.armarius/config.yaml`.",
                "code": f"armarius init --library-path {library_root}",
            },
            {
                "title": "3. Open the web UI",
                "body": "Launch the local dashboard and inspect your library in the browser.",
                "code": "armarius serve",
            },
        ],
        "tips_title": "What to do next",
        "tips": [
            "Drop PDFs into the configured library folder.",
            "Open the Library page to inspect scan results and stats.",
            "Open the Tutorial tab for the current workflow guide.",
            "If the screen is empty, confirm the folder really contains `.pdf` files.",
        ],
        "status_title": "Current setup",
        "status_lines": [
            f"Library path: {library_root}",
            "Web UI: http://localhost:8501",
            "Config file: ~/.armarius/config.yaml",
        ],
    }


def build_home_wizard_state(library_root: Path) -> dict[str, object]:
    """Build the onboarding workflow state for the home page.

    Args:
        library_root: Configured library path.

    Returns:
        Step-oriented state describing what the user can do next.
    """
    inbox_path = library_root / "_inbox"
    library_exists = library_root.exists() and library_root.is_dir()
    inbox_exists = inbox_path.exists() and inbox_path.is_dir()
    inbox_pdf_count = len(list(inbox_path.glob("*.pdf"))) if inbox_exists else 0

    if library_exists:
        library_status = "done"
        library_detail = f"Library path is ready: {library_root}"
    else:
        library_status = "pending"
        library_detail = f"Library path does not exist yet: {library_root}"

    if not library_exists:
        inbox_status = "blocked"
        inbox_detail = "Create or choose a valid library path first."
    elif inbox_pdf_count:
        inbox_status = "ready"
        inbox_detail = f"{inbox_pdf_count} PDFs waiting in inbox."
    else:
        inbox_status = "pending"
        inbox_detail = "Drop PDFs into _inbox to start the intake flow."

    if library_exists:
        review_status = "ready"
        review_detail = "Open Library → Intake to review, rename, and accept files."
    else:
        review_status = "blocked"
        review_detail = "Library review unlocks after the library path is valid."

    return {
        "steps": [
            {
                "key": "install",
                "title": "Install CLI",
                "status": "done",
                "detail": "The web UI is running, so the local toolchain is already available.",
                "action": "uv tool install --editable '.[web]'",
            },
            {
                "key": "library",
                "title": "Choose library",
                "status": library_status,
                "detail": library_detail,
                "action": f"armarius init --library-path {library_root}",
            },
            {
                "key": "inbox",
                "title": "Process inbox",
                "status": inbox_status,
                "detail": inbox_detail,
                "action": "armarius intake scan-inbox --normalize",
            },
            {
                "key": "review",
                "title": "Review results",
                "status": review_status,
                "detail": review_detail,
                "action": "armarius review set-state <blob_id> accepted",
            },
        ]
    }


def build_sidebar_workflow_steps(library_root: Path, current_page: str, current_room: str) -> list[dict[str, object]]:
    """Build left-sidebar workflow navigation steps.

    Args:
        library_root: Active library path.
        current_page: Current top-level page.
        current_room: Current library room.

    Returns:
        Ordered steps for advancing through the product workflow.
    """
    wizard = build_home_wizard_state(library_root)
    inbox_step = next(step for step in wizard["steps"] if step["key"] == "inbox")
    review_step = next(step for step in wizard["steps"] if step["key"] == "review")
    steps: list[dict[str, object]] = [
        {"title": "1. 先看狀態" if current_page or True else "1. Start here", "page": "dashboard", "room": "", "status": "done", "summary": "See the overall workspace status and next step."},
        {"title": "2. 看文獻庫", "page": "library", "room": "statistics", "status": wizard["steps"][1]["status"], "summary": "Check the current library and scan result."},
        {"title": "3. 收新文件", "page": "library", "room": "intake", "status": inbox_step["status"], "summary": "Import PDFs and整理可用材料。"},
        {"title": "4. 整理與確認", "page": "library", "room": "intake", "status": review_step["status"], "summary": "Review results and fix files when needed."},
        {"title": "5. 做重點分析", "page": "paradigm_analysis", "room": "", "status": "ready", "summary": "Generate structured reading notes."},
        {"title": "6. 整理成輸出", "page": "concerto_synthesis", "room": "", "status": "ready", "summary": "Turn analysis into a usable output draft."},
    ]

    for step in steps:
        step["is_current"] = step["page"] == current_page and (not step["room"] or step["room"] == current_room)
        step["is_next"] = False

    current_index = next((index for index, step in enumerate(steps) if step["is_current"]), 0)
    next_index = current_index + 1 if current_index + 1 < len(steps) else current_index
    if current_index != next_index:
        steps[next_index]["is_next"] = True

    return steps


def run_home_wizard_action(step_key: str, config: ArmariusConfig, intake_service: IntakeService | None, library_root: Path) -> dict[str, str]:
    """Execute one home-page wizard step.

    Args:
        step_key: Wizard step identifier.
        config: Application config.
        intake_service: Intake service when required by the step.
        library_root: Active library path.

    Returns:
        Structured outcome for UI feedback or navigation.
    """
    if step_key == "install":
        return {
            "outcome": "info",
            "message": "The web app is already running; the CLI runtime is available.",
        }

    if step_key == "library":
        config.set("library.root_path", str(library_root))
        config.save()
        return {
            "outcome": "success",
            "message": f"Library path saved: {library_root}",
        }

    if step_key == "inbox":
        if intake_service is None:
            return {"outcome": "error", "message": "Intake service is unavailable."}
        results = intake_service.intake_inbox()
        accepted = [record for record in results if record.ingest_state == "accepted"]
        for record in accepted:
            intake_service.normalize_blob(record.document_blob_id)
        return {
            "outcome": "success",
            "message": f"Processed {len(results)} files; normalized {len(accepted)} accepted PDFs.",
        }

    if step_key == "review":
        return {
            "outcome": "navigate",
            "message": "Opening Library intake review.",
            "page": "library",
            "room": "intake",
        }

    return {"outcome": "error", "message": f"Unsupported wizard step: {step_key}"}


def build_dashboard_overview(locale: str, queue_summary: dict[str, Any], inbox_count: int, analyses_count: int, synthesis_count: int) -> dict[str, object]:
    """Build an operations overview payload for the dashboard.

    Args:
        locale: Active locale.
        queue_summary: Queue counts from the intake service.
        inbox_count: Count of PDFs waiting in inbox.
        analyses_count: Count of analysis outputs.
        synthesis_count: Count of synthesis outputs.

    Returns:
        Structured dashboard overview payload.
    """
    zh = locale == "zh-TW"
    headline_metrics = [
        {"label": "Blob 總數" if zh else "Total blobs", "value": str(queue_summary["total_blobs"])},
        {"label": "可分析" if zh else "Ready for analysis", "value": str(queue_summary["processing"]["ready_for_analysis"])},
        {"label": "待 OCR" if zh else "Needs OCR", "value": str(queue_summary["ingest"]["needs_ocr"])},
        {"label": "卡住項目" if zh else "Stale items", "value": str(queue_summary["stale"]["total"])},
    ]
    queues = [
        {"label": "收件匣待處理" if zh else "Inbox pending", "count": str(inbox_count), "target": "statistics"},
        {"label": "待審核" if zh else "Needs review", "count": str(queue_summary["ingest"]["quarantine"]), "target": "intake"},
        {"label": "待 OCR" if zh else "Needs OCR", "count": str(queue_summary["ingest"]["needs_ocr"]), "target": "intake"},
        {"label": "可分析" if zh else "Ready for analysis", "count": str(queue_summary["processing"]["ready_for_analysis"]), "target": "intake"},
        {"label": "分析完成" if zh else "Analysis outputs", "count": str(analyses_count), "target": "paradigm_analysis"},
        {"label": "可匯總" if zh else "Ready for synthesis", "count": str(synthesis_count), "target": "concerto_synthesis"},
    ]
    next_actions = [
        {"title": "先處理收件匣" if zh else "Process inbox first", "detail": "新進 PDF 先進 intake 流程。" if zh else "New PDFs should enter intake first.", "target": "intake", "key": "process_inbox"},
        {"title": "清掉待 OCR 與待審核" if zh else "Clear OCR and review backlog", "detail": "避免文件卡在中間狀態。" if zh else "Reduce files stuck in intermediate states.", "target": "intake", "key": "clear_backlog"},
        {"title": "再進分析與匯總" if zh else "Continue with analysis and synthesis", "detail": "等 ready_for_analysis 累積後再往下推進。" if zh else "Move forward after enough files are ready for analysis.", "target": "paradigm_analysis", "key": "continue_downstream"},
    ]
    return {"headline_metrics": headline_metrics, "queues": queues, "next_actions": next_actions, "stale": queue_summary["stale"]}


def render_home_page(config: ArmariusConfig, i18n: I18n, library_root: Path) -> None:
    """Render the dashboard as a concise research workspace overview.

    Args:
        config: Application configuration.
        i18n: Translation helper.
        library_root: Configured library path.
    """
    db = ArmariusDatabase()
    intake_service = IntakeService(db, PDFProcessor(), library_root)

    with st.spinner(i18n.t("messages.scanning")):
        pdf_list = scan_library(library_root, config.recursive_scan)

    stats = get_stats(pdf_list)
    workflow_name = "default"
    workflow_config_file = library_root / "_armarius-config.toml"
    if workflow_config_file.exists():
        try:
            with open(workflow_config_file, "r", encoding="utf-8") as file_handle:
                workflow_data = toml.load(file_handle)
            workflow_name = workflow_data.get("library", {}).get("workflow", "default")
        except Exception:
            workflow_name = "default"

    workflow = LibraryWorkflow(library_root, workflow_name=workflow_name)
    workflow_status = workflow.get_status()
    inbox_path = workflow.get_input_folder()
    inbox_count = len(list(inbox_path.glob("*.pdf"))) if inbox_path.exists() else 0
    analyses_path = Path.home() / ".armarius" / "analyses"
    analyses_count = len(list(analyses_path.rglob("*.md"))) if analyses_path.exists() else 0
    synthesis_path = library_root / "synthesis"
    synthesis_count = len(list(synthesis_path.rglob("*.md"))) if synthesis_path.exists() else 0

    queue_summary = intake_service.get_queue_summary()
    overview = build_dashboard_overview(i18n.locale, queue_summary, inbox_count, analyses_count, synthesis_count)
    ready_for_analysis = queue_summary["processing"]["ready_for_analysis"]

    st.header("Dashboard" if i18n.locale != "zh-TW" else "儀表板")

    with st.container(border=True):
        st.subheader(
            "Armarius is your research workspace"
            if i18n.locale != "zh-TW"
            else "Armarius 是你的研究工作台"
        )
        st.write(
            "Move from PDF intake to structured analysis and synthesis in one local workspace. Start here to understand your library health, what is ready, and what to do next."
            if i18n.locale != "zh-TW"
            else "在同一個本地工作區裡，從 PDF 收件一路走到結構化分析與綜整。先在這裡看清楚文獻庫狀態、哪些材料已經可用，以及下一步該做什麼。"
        )
        st.markdown(
            """- Start in **Library** to intake, normalize, and review source material.
- Continue to **Analysis** when papers are ready for structured reading.
- Use **Synthesis** when you want an output draft for a reader or task."""
            if i18n.locale != "zh-TW"
            else """- 從 **Library** 開始收件、正規化與審查來源材料。
- 當文獻準備好後，再到 **Analysis** 做結構化閱讀。
- 當你要整理成可交付給讀者或任務使用的初稿時，再到 **Synthesis**。"""
        )

    metric_cols = st.columns(len(overview["headline_metrics"]))
    for column, metric in zip(metric_cols, overview["headline_metrics"]):
        with column:
            st.metric(metric["label"], metric["value"])

    action_col, readiness_col, workflow_col = st.columns([1.25, 1.25, 1])

    with action_col:
        with st.container(border=True):
            st.markdown("**Next actions**" if i18n.locale != "zh-TW" else "**下一步建議**")
            actions = [
                "Open Library → Intake to process inbox PDFs." if i18n.locale != "zh-TW" else "前往 Library → Intake 處理收件匣 PDF。",
                "Review accepted and normalized records before analysis." if i18n.locale != "zh-TW" else "在進分析前，先檢查 accepted 與 normalized 結果。",
                "Move to Analysis when enough papers are ready." if i18n.locale != "zh-TW" else "當可用文獻累積足夠時，再前往 Analysis。",
            ]
            for item in actions:
                st.markdown(f"- {item}")
            st.caption(
                "Actual operational actions remain in Library → Intake."
                if i18n.locale != "zh-TW"
                else "真正的執行動作保留在 Library → Intake。"
            )
            if st.button("Go to Library" if i18n.locale != "zh-TW" else "前往 Library", key="dashboard-go-library", width="stretch", type="primary"):
                st.session_state["page"] = "library"
                st.session_state["dashboard_target_room"] = "intake"
                st.rerun()

    with readiness_col:
        with st.container(border=True):
            st.markdown("**Research readiness**" if i18n.locale != "zh-TW" else "**研究準備度**")
            st.markdown(
                f"""- {stats['total_count']} PDFs in workspace
- {queue_summary['total_blobs']} tracked intake records
- {ready_for_analysis} items ready for analysis
- {synthesis_count} synthesis outputs available"""
                if i18n.locale != "zh-TW"
                else f"""- 工作區中共有 {stats['total_count']} 份 PDF
- 共有 {queue_summary['total_blobs']} 筆收件追蹤紀錄
- 已有 {ready_for_analysis} 筆可進入分析
- 目前已有 {synthesis_count} 份 synthesis 輸出"""
            )

    with workflow_col:
        with st.container(border=True):
            st.markdown("**Current workflow**" if i18n.locale != "zh-TW" else "**目前工作流**")
            st.write(f"{workflow_name} · {workflow_status.name.lower()}")
            st.caption(
                "Dashboard stays light on purpose. Detailed execution and queue actions stay in Library."
                if i18n.locale != "zh-TW"
                else "Dashboard 刻意保持精簡；詳細執行與佇列操作都留在 Library。"
            )

    st.subheader("Recent intake" if i18n.locale != "zh-TW" else "最近收件")
    recent_blobs = intake_service.list_recent_blobs(limit=10)
    if recent_blobs:
        st.dataframe(
            [
                {
                    "Blob ID": row["id"],
                    "Source": row["source_filename"],
                    "Managed": row["managed_filename"],
                    "State": row["ingest_state"],
                    "DOI": row["canonical_doi"] or "",
                    "Title": row["canonical_title"] or "",
                }
                for row in recent_blobs
            ],
            width="stretch",
            hide_index=True,
        )
        st.caption(
            "Execution actions stay in Library → Intake."
            if i18n.locale != "zh-TW"
            else "真正的執行動作保留在 Library → Intake。"
        )
    else:
        st.info("No intake records yet." if i18n.locale != "zh-TW" else "目前還沒有收件紀錄。")

def render_library_page(config: ArmariusConfig, i18n: I18n, library_root: Path) -> None:
    """Render the main library workspace page.

    Args:
        config: Application configuration.
        i18n: Translation helper.
        library_root: Configured library path.
    """
    workflow_name = "default"
    config_file = library_root / "_armarius-config.toml"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as file_handle:
                config_data = toml.load(file_handle)
            workflow_name = config_data.get("library", {}).get("workflow", "default")
        except Exception:
            pass

    workflow = LibraryWorkflow(library_root, workflow_name=workflow_name)
    status = workflow.get_status()

    with st.spinner(i18n.t("messages.scanning")):
        pdf_list = scan_library(library_root, config.recursive_scan)

    target_room = st.session_state.pop("dashboard_target_room", None)
    if st.session_state.get("page") == "library" and target_room:
        room_messages = {
            "statistics": (
                "Opened from Dashboard: start with library stats and intake queue."
                if i18n.locale != "zh-TW"
                else "已從儀表板導來：先看文獻統計與收件狀態。"
            ),
            "intake": (
                "Opened from Dashboard: continue with intake operations here."
                if i18n.locale != "zh-TW"
                else "已從儀表板導來：接著在這裡進行 intake 操作。"
            ),
            "catalog": (
                "Opened from Dashboard: review the catalog room next."
                if i18n.locale != "zh-TW"
                else "已從儀表板導來：下一步請看目錄室。"
            ),
            "analysis": (
                "Opened from Dashboard: continue with paradigm analysis here."
                if i18n.locale != "zh-TW"
                else "已從儀表板導來：接著可在這裡進行派典分析。"
            ),
            "synthesis": (
                "Opened from Dashboard: continue with concerto synthesis here."
                if i18n.locale != "zh-TW"
                else "已從儀表板導來：接著可在這裡進行協奏匯總。"
            ),
        }
        st.info(room_messages[target_room])

    if not pdf_list:
        st.warning(i18n.t("errors.no_pdfs"))
        st.info(i18n.t("errors.place_pdfs", path=library_root))
        return

    stats = get_stats(pdf_list)

    room_options = [
        ("intake", "Intake" if i18n.locale != "zh-TW" else "收件"),
        ("statistics", i18n.t("rooms.statistics_title")),
        ("catalog", i18n.t("rooms.catalog_title")),
        ("analysis", i18n.t("rooms.restoration_title")),
        ("synthesis", i18n.t("rooms.guide_title")),
    ]
    current_room = target_room or st.session_state.get("library_room", "intake")
    room_ids = [room_id for room_id, _ in room_options]
    if current_room not in room_ids:
        current_room = "statistics"
    selected_room = st.radio(
        "Library room" if i18n.locale != "zh-TW" else "Library 房間",
        options=room_ids,
        index=room_ids.index(current_room),
        format_func=lambda room_id: dict(room_options)[room_id],
        horizontal=True,
        key="library-room-selector",
    )
    st.session_state["library_room"] = selected_room

    if selected_room == "intake":
        from armarius.database import ArmariusDatabase
        db = ArmariusDatabase()
        intake_service = IntakeService(db, PDFProcessor(), library_root)
        queue_presets = {
            "all": {
                "label": "All intake" if i18n.locale != "zh-TW" else "全部 intake",
                "states": ["accepted", "quarantine", "needs_ocr", "rejected"],
                "processing": None,
            },
            "review": {
                "label": "Needs review" if i18n.locale != "zh-TW" else "待審核",
                "states": ["quarantine"],
                "processing": ["quarantined"],
            },
            "ocr": {
                "label": "Needs OCR" if i18n.locale != "zh-TW" else "待 OCR",
                "states": ["needs_ocr"],
                "processing": ["needs_ocr"],
            },
            "analysis": {
                "label": "Ready for analysis" if i18n.locale != "zh-TW" else "可分析",
                "states": ["accepted"],
                "processing": ["ready_for_analysis"],
            },
        }
        selected_queue = st.selectbox(
            "Queue view" if i18n.locale != "zh-TW" else "佇列視圖",
            options=list(queue_presets.keys()),
            format_func=lambda key: queue_presets[key]["label"],
        )
        preset = queue_presets[selected_queue]
        recent_blobs = intake_service.list_recent_blobs(
            limit=50,
            states=preset["states"],
            processing_stages=preset["processing"],
        )
        action_col, info_col = st.columns([1, 2])
        with action_col:
            if st.button("Process inbox" if i18n.locale != "zh-TW" else "處理收件匣", width="stretch"):
                results = intake_service.intake_inbox()
                accepted = [record for record in results if record.ingest_state == "accepted"]
                for record in accepted:
                    intake_service.normalize_blob(record.document_blob_id)
                st.success(
                    f"Processed {len(results)} files; normalized {len(accepted)} accepted PDFs."
                    if i18n.locale != "zh-TW"
                    else f"已處理 {len(results)} 份檔案，並正規化 {len(accepted)} 份可接受 PDF。"
                )
                st.rerun()
        with info_col:
            st.caption(
                "Accepted files are normalized automatically; needs-OCR and quarantine stay visible for review."
                if i18n.locale != "zh-TW"
                else "可接受檔案會自動正規化；需 OCR 與隔離檔案會保留供後續檢查。"
            )
        if recent_blobs:
            st.dataframe(
                [
                    {
                        "Blob ID": row["id"],
                        "Source": row["source_filename"],
                        "Managed": row["managed_filename"],
                        "State": row["ingest_state"],
                        "Stage": row["processing_stage"],
                        "DOI": row["canonical_doi"] or "",
                        "Title": row["canonical_title"] or "",
                    }
                    for row in recent_blobs
                ],
                width="stretch",
                hide_index=True,
            )
            exception_count = sum(1 for row in recent_blobs if row["ingest_state"] in {"quarantine", "needs_ocr", "rejected"})
            accepted_count = sum(1 for row in recent_blobs if row["ingest_state"] == "accepted")
            stat_col1, stat_col2 = st.columns(2)
            with stat_col1:
                st.metric("Exceptions" if i18n.locale != "zh-TW" else "異常件", exception_count)
            with stat_col2:
                st.metric("Accepted" if i18n.locale != "zh-TW" else "已接受", accepted_count)

            batch_ids = st.multiselect(
                "Batch select" if i18n.locale != "zh-TW" else "批次選取",
                options=[row["id"] for row in recent_blobs],
                format_func=lambda blob_id: next(row["managed_filename"] for row in recent_blobs if row["id"] == blob_id),
            )
            batch_target_state = st.selectbox(
                "Batch move to" if i18n.locale != "zh-TW" else "批次移到",
                options=["accepted", "quarantine", "needs_ocr", "rejected"],
                index=0,
                key="batch-target-state",
            )
            batch_col1, batch_col2, batch_col3 = st.columns(3)
            with batch_col1:
                if st.button("Batch update state" if i18n.locale != "zh-TW" else "批次更新狀態", width="stretch", disabled=not batch_ids):
                    for blob_id in batch_ids:
                        intake_service.update_ingest_state(blob_id, batch_target_state)
                    st.success(
                        f"Updated {len(batch_ids)} blobs to {batch_target_state}."
                        if i18n.locale != "zh-TW"
                        else f"已將 {len(batch_ids)} 個 blob 更新為 {batch_target_state}。"
                    )
                    st.rerun()
            with batch_col2:
                if st.button("Batch rename" if i18n.locale != "zh-TW" else "批次重新命名", width="stretch", disabled=not batch_ids):
                    for blob_id in batch_ids:
                        intake_service.apply_filename(blob_id)
                    st.success(
                        f"Renamed {len(batch_ids)} blobs."
                        if i18n.locale != "zh-TW"
                        else f"已重新命名 {len(batch_ids)} 個 blob。"
                    )
                    st.rerun()
            with batch_col3:
                if st.button("Batch retry normalize" if i18n.locale != "zh-TW" else "批次重跑正規化", width="stretch", disabled=not batch_ids):
                    intake_service.batch_normalize(batch_ids)
                    st.success(
                        f"Normalized {len(batch_ids)} blobs."
                        if i18n.locale != "zh-TW"
                        else f"已正規化 {len(batch_ids)} 個 blob。"
                    )
                    st.rerun()

            selected_blob = st.selectbox(
                "Inspect blob" if i18n.locale != "zh-TW" else "檢視 blob",
                options=[row["id"] for row in recent_blobs],
                format_func=lambda blob_id: next(row["managed_filename"] for row in recent_blobs if row["id"] == blob_id),
            )
            detail = intake_service.get_blob_detail(selected_blob)
            detail_col1, detail_col2 = st.columns([2, 1])
            with detail_col1:
                st.markdown("**Trace**" if i18n.locale != "zh-TW" else "**追蹤資訊**")
                with st.expander("Show raw trace" if i18n.locale != "zh-TW" else "展開原始追蹤資訊", expanded=False):
                    st.code(
                        json.dumps(detail, ensure_ascii=False, indent=2, default=str),
                        language="json",
                    )
                artifact_paths = [artifact["path"] for artifact in detail.get("artifacts", [])]
                markdown_artifacts = [path for path in artifact_paths if path.endswith("document.md")]
                manifest_artifacts = [path for path in artifact_paths if path.endswith("manifest.json")]
                table_artifacts = [path for path in artifact_paths if "/tables/" in path]
                image_artifacts = [path for path in artifact_paths if "/images/" in path]
                if markdown_artifacts:
                    with st.expander("Markdown preview" if i18n.locale != "zh-TW" else "Markdown 預覽", expanded=False):
                        try:
                            st.code(Path(markdown_artifacts[0]).read_text(encoding="utf-8"), language="markdown")
                        except Exception as exc:
                            st.error(str(exc))
                if manifest_artifacts:
                    with st.expander("Manifest preview" if i18n.locale != "zh-TW" else "Manifest 預覽", expanded=False):
                        try:
                            st.json(json.loads(Path(manifest_artifacts[0]).read_text(encoding="utf-8")))
                        except Exception as exc:
                            st.error(str(exc))
                if table_artifacts:
                    with st.expander("Tables" if i18n.locale != "zh-TW" else "表格", expanded=False):
                        for table_path in table_artifacts:
                            st.write(table_path)
                if image_artifacts:
                    with st.expander("Images" if i18n.locale != "zh-TW" else "圖片", expanded=False):
                        for image_path in image_artifacts:
                            st.write(image_path)
            with detail_col2:
                st.markdown("**Review actions**" if i18n.locale != "zh-TW" else "**審查動作**")
                if st.button("Apply rename" if i18n.locale != "zh-TW" else "套用重新命名", width="stretch"):
                    intake_service.apply_filename(selected_blob)
                    st.success("Rename applied." if i18n.locale != "zh-TW" else "已套用重新命名。")
                    st.rerun()
                review_note = st.text_area("Review note" if i18n.locale != "zh-TW" else "審查備註", key="review-note")
                review_reason = st.text_input("Reason override" if i18n.locale != "zh-TW" else "原因覆寫", key="review-reason")
                review_target = st.selectbox(
                    "Move to state" if i18n.locale != "zh-TW" else "移到狀態",
                    options=["accepted", "quarantine", "needs_ocr", "rejected"],
                    index=0,
                    key="review-target-state",
                )
                if st.button("Update state" if i18n.locale != "zh-TW" else "更新狀態", width="stretch"):
                    intake_service.update_ingest_state(selected_blob, review_target, review_note=review_note or None, reason=review_reason or None)
                    st.success(
                        f"Moved to {review_target}."
                        if i18n.locale != "zh-TW"
                        else f"已移動到 {review_target}。"
                    )
                    st.rerun()
                if st.button("Retry normalize" if i18n.locale != "zh-TW" else "重跑正規化", width="stretch"):
                    try:
                        intake_service.normalize_blob(selected_blob)
                        st.success("Normalization completed." if i18n.locale != "zh-TW" else "正規化完成。")
                    except Exception as exc:
                        st.error(str(exc))
        else:
            st.info("No intake records yet." if i18n.locale != "zh-TW" else "目前還沒有收件紀錄。")

    elif selected_room == "statistics":
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(i18n.t("stats.total_pdfs"), stats["total_count"])
        with col2:
            st.metric(i18n.t("stats.readable"), stats["readable_count"])
        with col3:
            st.metric(i18n.t("stats.unreadable"), stats["unreadable_count"])
        with col4:
            st.metric(i18n.t("stats.total_size"), f"{stats['total_size_mb']:.1f} MB")
        st.info(i18n.t("rooms.statistics.input_folder_info"))
        st.code(str(workflow.get_input_folder()), language="bash")
        st.caption(i18n.t("rooms.statistics.input_folder_caption"))
        st.divider()
        search_query = st.text_input(i18n.t("search.label"), placeholder=i18n.t("search.placeholder"))
        filtered_list = pdf_list
        if search_query:
            filtered_list = [pdf for pdf in pdf_list if search_query.lower() in pdf.filename.lower()]
        col1, col2 = st.columns([3, 1])
        with col1:
            st.caption(i18n.t("search.showing", count=len(filtered_list), total=len(pdf_list)))
        with col2:
            items_per_page = st.selectbox(
                i18n.t("rooms.statistics.items_per_page"), options=[10, 25, 50, 100], index=0, key="items_per_page"
            )
        pagination_signature = (search_query, items_per_page)
        if st.session_state.get("pagination_signature") != pagination_signature:
            st.session_state.current_page = 1
            st.session_state["pagination_signature"] = pagination_signature

        total_items = len(filtered_list)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages if total_pages > 0 else 1
        start_idx = (st.session_state.current_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_list = filtered_list[start_idx:end_idx]
        df_data = []
        for pdf in paginated_list:
            pdf_status = i18n.t("table.status_readable") if pdf.is_readable else i18n.t("table.status_unreadable")
            df_data.append(
                {
                    i18n.t("table.status"): pdf_status,
                    i18n.t("table.filename"): pdf.filename,
                    i18n.t("table.size"): format_file_size(pdf.size_bytes),
                    i18n.t("table.pages"): pdf.page_count if pdf.page_count else "N/A",
                    i18n.t("table.modified"): format_datetime(pdf.modified_time),
                    i18n.t("table.path"): str(pdf.path.relative_to(library_root)) if pdf.path.is_relative_to(library_root) else str(pdf.path),
                }
            )
        df = pd.DataFrame(df_data)
        st.dataframe(
            df,
            width="stretch",
            hide_index=True,
            column_config={
                i18n.t("table.status"): st.column_config.TextColumn(width="small"),
                i18n.t("table.filename"): st.column_config.TextColumn(width="medium"),
                i18n.t("table.size"): st.column_config.TextColumn(width="small"),
                i18n.t("table.pages"): st.column_config.TextColumn(width="small"),
                i18n.t("table.modified"): st.column_config.TextColumn(width="medium"),
                i18n.t("table.path"): st.column_config.TextColumn(width="large"),
            },
        )
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("⬅️ " + i18n.t("rooms.statistics.previous_page"), disabled=st.session_state.current_page <= 1):
                    st.session_state.current_page -= 1
                    st.rerun()
            with col2:
                st.caption(i18n.t("rooms.statistics.page_info", current=st.session_state.current_page, total=total_pages))
            with col3:
                if st.button(i18n.t("rooms.statistics.next_page") + " ➡️", disabled=st.session_state.current_page >= total_pages):
                    st.session_state.current_page += 1
                    st.rerun()
        errors = [pdf for pdf in filtered_list if not pdf.is_readable]
        if errors:
            with st.expander(i18n.t("messages.unreadable_files", count=len(errors)), expanded=False):
                for pdf in errors:
                    st.text(f"❌ {pdf.filename}")
                    if pdf.error:
                        st.caption(f"   {i18n.t('messages.error_label')}: {pdf.error}")

    elif selected_room == "catalog":
        from armarius.database import ArmariusDatabase
        db = ArmariusDatabase()
        render_catalog_room(config, db, library_root, workflow, status, i18n)

    elif selected_room == "analysis":
        st.info(
            "Open the dedicated Paradigm Analysis page from the sidebar for the full workflow."
            if i18n.locale != "zh-TW"
            else "完整流程請從側邊欄打開獨立的「派典分析」頁面。"
        )

    else:
        st.info(
            "Open the dedicated Concerto Synthesis page from the sidebar for the full workflow."
            if i18n.locale != "zh-TW"
            else "完整流程請從側邊欄打開獨立的「協奏匯總」頁面。"
        )


def build_sidebar_support_pages(locale: str) -> list[tuple[str, str]]:
    """Build secondary sidebar navigation items."""
    zh = locale == "zh-TW"
    return [
        ("tutorial", "怎麼使用" if zh else "How It Works"),
        ("catalog_assistant", "整理方式參考" if zh else "Organization Help"),
        ("settings", "設定" if zh else "Settings"),
    ]


def pick_page(i18n: I18n) -> str:
    """Render secondary sidebar navigation and return the selected page id."""
    current = st.session_state.get("page", "dashboard")
    support_pages = build_sidebar_support_pages(i18n.locale)
    support_ids = [page_id for page_id, _ in support_pages]
    if current not in {"dashboard", "library", "paradigm_analysis", "concerto_synthesis", *support_ids}:
        current = "dashboard"

    st.sidebar.caption("Other" if i18n.locale != "zh-TW" else "其他")
    for page_id, label in support_pages:
        active = current == page_id
        if st.sidebar.button(
            ("● " if active else "") + label,
            key=f"support-{page_id}",
            width="stretch",
            type="primary" if active else "secondary",
        ):
            st.session_state["page"] = page_id
            return page_id
    return current


def render_paradigm_analysis_page(i18n: I18n) -> None:
    """Render the dedicated paradigm analysis page."""
    st.header("Analysis" if i18n.locale != "zh-TW" else "重點分析")
    st.caption(
        "Use this step after your materials are ready. In the current version, you choose a paper folder and one or more analysis perspectives, then start generating analysis cards."
        if i18n.locale != "zh-TW"
        else "當材料準備好之後，就用這一步。以目前版本來說，你會選擇論文資料夾與一個或多個分析視角，然後開始生成分析卡。"
    )
    st.header(i18n.t("paradigm_analysis.step1_title"))
    from armarius.paradigm import ParadigmLoader
    paradigm_loader = ParadigmLoader()
    paradigms = paradigm_loader.list_paradigms()
    if not paradigms:
        st.warning(i18n.t("paradigm_analysis.paradigm_selector.no_paradigms_warning"))
        st.info(i18n.t("paradigm_analysis.paradigm_selector.no_paradigms_info"))
        return

    st.caption(
        "Select paradigms and a folder of papers to generate analysis cards."
        if i18n.locale != "zh-TW"
        else "選擇派典與論文資料夾，生成分析卡。"
    )
    with st.form("paradigm_analysis_page_form"):
        folder_path = st.text_input(
            i18n.t("paradigm_analysis.paper_selector.folder_path_placeholder"),
            placeholder="/path/to/your/papers",
            help=i18n.t("paradigm_analysis.paper_selector.folder_tip"),
        )
        paradigm_options = [f"{p['name']} ({p['type']})" for p in paradigms]
        selected_paradigms = st.multiselect(
            i18n.t("paradigm_analysis.paradigm_selector.select_placeholder"),
            paradigm_options,
            help=i18n.t("paradigm_analysis.lens_selector.caption"),
        )
        submitted = st.form_submit_button(
            "🎼 " + i18n.t("paradigm_analysis.summary.generate_button"),
            type="primary",
            width="stretch",
        )
        if submitted:
            if not folder_path:
                st.error(i18n.t("rooms.restoration.error_no_folder"))
            elif not selected_paradigms:
                st.error(i18n.t("rooms.restoration.error_no_paradigm"))
            else:
                st.success(i18n.t("rooms.restoration.success_started", count=len(selected_paradigms)))
                st.info(
                    "Next: review the generated analysis artifacts, then move to Concerto Synthesis when you want audience-shaped outputs."
                    if i18n.locale != "zh-TW"
                    else "下一步：先檢查生成的分析成果；當你要整理成面向特定受眾的輸出時，再前往 Concerto Synthesis。"
                )


def render_concerto_synthesis_page(i18n: I18n) -> None:
    """Render the dedicated concerto synthesis page."""
    st.header("Output Draft" if i18n.locale != "zh-TW" else "整理成輸出")
    st.caption(
        "Use this step after analysis when you want a more usable output draft. In the current version, you choose one analysis perspective and one output format, then start synthesis generation."
        if i18n.locale != "zh-TW"
        else "當你完成分析，想把內容整理成更可用的初稿時，就用這一步。以目前版本來說，你會選一個分析視角與一個輸出格式，然後開始生成匯總內容。"
    )
    st.header(i18n.t("concerto_synthesis.step1_title"))
    from armarius.paradigm import ConcertoLoader, ParadigmLoader
    concerti = ConcertoLoader().list_concerti()
    paradigms = ParadigmLoader().list_paradigms()
    if not concerti:
        st.warning(i18n.t("concerto_synthesis.concerto_selector.no_concerti_warning"))
        st.info(i18n.t("concerto_synthesis.concerto_selector.no_concerti_info"))
        return
    if not paradigms:
        st.warning(i18n.t("concerto_synthesis.paradigm_selector.no_paradigms_warning"))
        return

    st.caption(
        "Select a paradigm and concerto to generate a synthesis output."
        if i18n.locale != "zh-TW"
        else "選擇派典與 concerto，生成匯總輸出。"
    )
    with st.form("concerto_synthesis_page_form"):
        paradigm_filter_options = [f"{p['name']} ({p['type']})" for p in paradigms]
        selected_paradigm_filter = st.selectbox(
            i18n.t("concerto_synthesis.paradigm_selector.select_placeholder"),
            paradigm_filter_options,
            help=i18n.t("concerto_synthesis.card_selector.filter_title"),
        )
        concerto_options = [c["name"] for c in concerti]
        selected_concerto = st.selectbox(
            i18n.t("concerto_synthesis.concerto_selector.select_placeholder"),
            concerto_options,
            help=i18n.t("concerto_synthesis.concerto_selector.details_title"),
        )
        submitted = st.form_submit_button(
            "🎭 " + i18n.t("concerto_synthesis.summary.generate_button"),
            type="primary",
            width="stretch",
        )
        if submitted:
            st.success(i18n.t("rooms.guide.success_started", concerto=selected_concerto))
            st.info(
                "Next: refine the synthesis output against your writing target, and return to Analysis or Library if the source base still feels thin."
                if i18n.locale != "zh-TW"
                else "下一步：請依你的寫作目標繼續修整 synthesis 結果；如果來源材料仍太薄，回到 Analysis 或 Library 補強。"
            )


def render_settings_page(config: ArmariusConfig, i18n: I18n, library_root: Path) -> None:
    """Render a dedicated settings page."""
    st.header("Settings" if i18n.locale != "zh-TW" else "設定")
    st.caption(
        "Use this page only when you need to confirm the active workspace, config file location, language, or theme. It is not part of the main research flow."
        if i18n.locale != "zh-TW"
        else "只有在你要確認目前工作區、設定檔位置、語言或主題時，才需要來這一頁。它不屬於主要研究流程。"
    )
    st.write(
        "Manage app preferences and inspect the current workspace here."
        if i18n.locale != "zh-TW"
        else "在這裡管理應用程式偏好並查看目前工作區。"
    )

    st.subheader("Workspace" if i18n.locale != "zh-TW" else "目前工作區")
    st.code(str(library_root), language="text")
    st.caption(
        "Library switching is disabled in the current installed-app model."
        if i18n.locale != "zh-TW"
        else "目前安裝版模型不提供 library switching。"
    )

    st.subheader("Configuration" if i18n.locale != "zh-TW" else "設定檔")
    st.code(str(config.config_path), language="text")
    st.caption(
        "Recursive scan is treated as the current default and is not exposed as a user option here."
        if i18n.locale != "zh-TW"
        else "遞迴掃描視為目前產品預設，因此這裡不再顯示成使用者選項。"
    )

    st.subheader("Preferences" if i18n.locale != "zh-TW" else "偏好")
    render_sidebar_settings(config, i18n)


def main():
    """Main Streamlit app with i18n and theme support."""
    # Load config
    config = ArmariusConfig()

    # Initialize session state from config
    if "locale" not in st.session_state:
        st.session_state.locale = config.get("i18n.locale", "zh-TW")
    if "theme" not in st.session_state:
        st.session_state.theme = config.get("theme.mode", "light")
    i18n = I18n(st.session_state.locale)

    # Set page config
    st.set_page_config(
        page_title=i18n.t("page.title"),
        page_icon="📇",
        layout="wide",
    )

    # Apply theme
    apply_theme(st.session_state.theme)

    st.title(i18n.t("page.title"))
    st.caption(i18n.t("page.subtitle"))

    # Check config exists
    if not config.config_path.exists():
        st.error(i18n.t("errors.config_not_found"))
        st.code("armarius init", language="bash")
        st.stop()

    # Prioritize default_path from config, fallback to library_root
    default_path = config.get("library.default_path")
    if default_path:
        library_root = Path(default_path).expanduser()
    else:
        library_root = config.library_root

    # Check library exists
    if not library_root.exists():
        st.error(i18n.t("errors.library_not_found", path=library_root))
        st.info(i18n.t("errors.run_init"))
        st.stop()

    # Sidebar: workflow navigator + page navigation only
    with st.sidebar:
        st.header("What to do" if i18n.locale != "zh-TW" else "現在要做什麼")
        current_page = st.session_state.get("page", "dashboard")
        current_room = st.session_state.get("library_room", "")
        workflow_steps = build_sidebar_workflow_steps(library_root, current_page=current_page, current_room=current_room)
        status_labels = {
            "done": "Done" if i18n.locale != "zh-TW" else "已完成",
            "ready": "Ready" if i18n.locale != "zh-TW" else "可推進",
            "pending": "Pending" if i18n.locale != "zh-TW" else "待處理",
            "blocked": "Blocked" if i18n.locale != "zh-TW" else "未解鎖",
        }
        status_icons = {"done": "✅", "ready": "🟡", "pending": "⚪", "blocked": "⛔"}
        for step in workflow_steps:
            badges: list[str] = [f"{status_icons[step['status']]} {status_labels[step['status']]}"]
            if step["is_current"]:
                badges.append("Now" if i18n.locale != "zh-TW" else "現在")
            elif step["is_next"]:
                badges.append("Next" if i18n.locale != "zh-TW" else "接下來")
            st.caption(" · ".join(badges))
            button_type = "primary" if step["is_current"] or step["is_next"] else "secondary"
            if st.button(step["title"], key=f"workflow-step-{step['title']}", width="stretch", disabled=step["status"] == "blocked", type=button_type):
                st.session_state["page"] = step["page"]
                if step["room"]:
                    st.session_state["dashboard_target_room"] = step["room"]
                st.rerun()
            summary = step["summary"]
            if i18n.locale == "zh-TW":
                summary_map = {
                    "Home dashboard and workflow snapshot.": "首頁儀表板與流程摘要。",
                    "Library folder exists and scan status is visible.": "文獻資料夾存在，且可查看掃描狀態。",
                    "Inbox PDFs are imported and accepted files are normalized.": "將收件匣 PDF 匯入，並正規化可接受檔案。",
                    "Review blob state, apply rename, and retry normalize if needed.": "檢查 blob 狀態、套用重新命名，必要時重跑正規化。",
                    "Generate analysis cards from selected paradigms.": "依選定派典產生分析卡。",
                    "Generate synthesis output from paradigm results.": "依派典結果產生匯總輸出。",
                }
                summary = summary_map.get(summary, summary)
            st.caption(summary)
        st.divider()
        st.caption("Current workspace" if i18n.locale != "zh-TW" else "目前工作區")
        st.code(str(library_root), language="text")
        st.caption(
            f"Workflow: {workflow_name} · {workflow_status.name.lower()}"
            if i18n.locale != "zh-TW"
            else f"工作流：{workflow_name} · {workflow_status.name.lower()}"
        )

    page = pick_page(i18n)

    if page == "dashboard":
        render_home_page(config, i18n, library_root)
    elif page == "library":
        render_library_page(config, i18n, library_root)
    elif page == "settings":
        render_settings_page(config, i18n, library_root)
    elif page == "paradigm_analysis":
        render_paradigm_analysis_page(i18n)
    elif page == "concerto_synthesis":
        render_concerto_synthesis_page(i18n)
    elif page == "tutorial":
        render_tutorial(i18n)
    elif page == "catalog_assistant":
        render_catalog_assistant(config, i18n)


def build_guide_content(locale: str) -> dict[str, object]:
    """Build short companion notes for the standalone workflow guide.

    Args:
        locale: Active locale.

    Returns:
        Structured summary content for the tutorial page.
    """
    if locale == "zh-TW":
        return {
            "legacy_title": "補充說明",
            "legacy_steps": [
                "上方單頁 Guide 講的是完整產品流程；左側 Workflow Navigator 則顯示目前 UI 真正可操作的步驟。",
                "現在的網頁主要覆蓋 Service Foundation、Intake，以及 Analysis / Synthesis 的部分流程。",
                "Catalog Assistant 仍是教學輔助入口，不是整體工作流的主導航頁。",
            ],
            "current_title": "目前建議操作順序",
            "current_steps": [
                "先看左側的『現在要做什麼』，確認目前最適合前進的步驟。",
                "到『文件與文獻』處理新進 PDF、確認 intake 結果，並把材料整理好。",
                "材料準備好後，再到『重點分析』生成分析卡。",
                "最後到『整理成輸出』把分析結果整理成更可用的初稿。",
            ],
            "updates_title": "為什麼現在這樣安排",
            "updates": [
                "完整流程已集中到單頁文件，避免 PRD、spec、roadmap 與 app 內文案各講一段。",
                "Tutorial 頁保留的是導讀與操作摘要，而不是再複寫一次完整流程文件。",
                "這樣後續更新工作流時，只需要先維護 `docs/workflow-guide.md` 這個主要來源。",
            ],
            "sources_title": "主要來源",
            "sources": [
                "`docs/workflow-guide.md`：完整流程的單頁說明與目前狀態總表。",
                "`docs/phase-0-quickstart.md`：早期 quick start 與 CLI/Web 啟動步驟。",
                "`docs/PRD.md`：M0/M1/M2/M6 等 milestone 與目前功能範圍。",
                "`docs/merge-roadmap/README.md`：舊設計與未來 roadmap。",
            ],
        }

    return {
        "legacy_title": "Companion notes",
        "legacy_steps": [
            "The standalone guide above describes the full product workflow, while the left workflow navigator shows what the current UI can actively execute.",
            "Today the web app mainly covers Service Foundation, Intake, and part of the Analysis and Synthesis flow.",
            "Catalog Assistant remains a tutorial helper rather than the main workflow entrypoint.",
        ],
        "current_title": "Recommended operating order",
        "current_steps": [
            "Start from the left-side 'What to do now' area to see the best next step.",
            "Go to 'Files & Library' to process new PDFs, inspect intake results, and clean up source material.",
            "Once materials are ready, go to 'Analysis' to generate analysis cards.",
            "Then go to 'Output Draft' to turn analysis into a more usable draft.",
        ],
        "updates_title": "Why the page is structured this way",
        "updates": [
            "The full workflow is now centralized in one standalone document instead of being split across PRD notes, specs, roadmap files, and inline UI copy.",
            "This Tutorial page now acts as a companion summary instead of restating the entire workflow document.",
            "Future workflow updates should start from `docs/workflow-guide.md` as the primary source of truth.",
        ],
        "sources_title": "Primary sources",
        "sources": [
            "`docs/workflow-guide.md`: single-page workflow description and current status summary.",
            "`docs/phase-0-quickstart.md`: early quick-start and CLI/Web launch steps.",
            "`docs/PRD.md`: milestones such as M0, M1, M2, and M6 plus current scope.",
            "`docs/merge-roadmap/README.md`: legacy design direction and forward roadmap.",
        ],
    }


def render_tutorial(i18n):
    """Render the tutorial page with i18n support."""
    st.title(i18n.t("tutorial.title"))
    st.header("Guide" if i18n.locale != "zh-TW" else "怎麼使用")
    st.caption(
        "Use this page when you are unsure what each step does. It explains the current product shape and matches the real implementation instead of the longer-term roadmap only."
        if i18n.locale != "zh-TW"
        else "當你不確定每一步到底在做什麼時，就看這一頁。它會說明目前產品真正可用的流程，而不是只有長期 roadmap。"
    )
    st.write(
        "This page explains what Armarius is, when to use each workspace page, and how the current product maps onto the larger research workflow."
        if i18n.locale != "zh-TW"
        else "這一頁用來說明 Armarius 是什麼、各頁面什麼時候該用，以及目前產品如何對應更完整的研究工作流。"
    )

    overview_col, concept_col = st.columns(2)
    with overview_col:
        with st.container(border=True):
            st.markdown("**Page map**" if i18n.locale != "zh-TW" else "**頁面地圖**")
            st.markdown(
                "- Dashboard: overall state and next actions\n- Library: source-material workspace\n- Analysis: paradigm-based reading\n- Synthesis: audience-shaped output\n- Settings: workspace and app preferences"
                if i18n.locale != "zh-TW"
                else "- Dashboard：看整體狀態與下一步\n- Library：整理來源材料\n- Analysis：做派典式閱讀\n- Synthesis：整理成面向受眾的輸出\n- Settings：管理工作區與 app 偏好"
            )
    with concept_col:
        with st.container(border=True):
            st.markdown("**Core concepts**" if i18n.locale != "zh-TW" else "**核心概念**")
            st.markdown(
                "- Paradigm = the reading perspective you apply to papers\n- Concerto = the output framing you apply for an audience\n- Guide = the stable map between the current product and the broader roadmap"
                if i18n.locale != "zh-TW"
                else "- Paradigm = 你套用在文獻上的閱讀視角\n- Concerto = 你為特定受眾安排輸出的框架\n- Guide = 把目前產品與更完整 roadmap 接起來的穩定地圖"
            )

    st.divider()
    if i18n.locale == "zh-TW":
        st.header("完整流程 Guide")
        st.caption("以下內容來自 `docs/workflow-guide.md`，作為目前整體工作流的單頁說明。")
    else:
        st.header("Full Workflow Guide")
        st.caption("The content below is loaded from `docs/workflow-guide.md` as the single-page workflow reference.")
    st.markdown(load_workflow_guide_markdown())

    guide = build_guide_content(i18n.locale)

    st.divider()
    st.header(guide["legacy_title"])
    for item in guide["legacy_steps"]:
        st.markdown(f"- {item}")

    st.divider()
    st.header(guide["current_title"])
    for item in guide["current_steps"]:
        st.markdown(f"- {item}")

    st.divider()
    st.header(guide["updates_title"])
    for item in guide["updates"]:
        st.markdown(f"- {item}")

    st.divider()
    st.header(guide["sources_title"])
    for item in guide["sources"]:
        st.markdown(f"- {item}")

    st.divider()
    st.header(i18n.t("tutorial.tips.title"))
    with st.expander(i18n.t("tutorial.tips.tip1_title"), expanded=True):
        st.write(i18n.t("tutorial.tips.tip1_desc"))
        st.code(i18n.t("tutorial.tips.tip1_prompt"), language="text")
    with st.expander(i18n.t("tutorial.tips.tip2_title")):
        st.write(i18n.t("tutorial.tips.tip2_desc"))
        st.code(i18n.t("tutorial.tips.tip2_prompt"), language="text")
    with st.expander(i18n.t("tutorial.tips.tip3_title")):
        st.write(i18n.t("tutorial.tips.tip3_desc"))

    st.divider()
    st.header(i18n.t("tutorial.coming_soon.title"))
    st.markdown(i18n.t("tutorial.coming_soon.phase1"))
    st.markdown(i18n.t("tutorial.coming_soon.phase2"))
    st.markdown(i18n.t("tutorial.coming_soon.phase3"))

    st.divider()
    st.header(i18n.t("tutorial.feedback.title"))
    st.write(i18n.t("tutorial.feedback.desc"))
    st.link_button(
        i18n.t("tutorial.feedback.link_text"),
        "https://github.com/matheme-justyn/armarius/issues",
        width="content"
    )


@st.cache_data(ttl=60)
def scan_library(library_root: Path, recursive: bool):
    """Scan library for PDFs (cached for 60 seconds).

    Args:
        library_root: Root directory to scan
        recursive: Scan subdirectories

    Returns:
        List of PDFInfo objects
    """
    scanner = PDFScanner(library_root, recursive=recursive)
    return scanner.scan()


def get_stats(pdf_list):
    """Calculate statistics from PDF list.

    Args:
        pdf_list: List of PDFInfo objects

    Returns:
        Statistics dictionary
    """
    scanner = PDFScanner(Path.home(), recursive=False)  # Dummy instance for stats
    return scanner.get_stats(pdf_list)


if __name__ == "__main__":
    main()
