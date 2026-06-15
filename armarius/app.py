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


def render_home_page(config: ArmariusConfig, i18n: I18n, library_root: Path) -> None:
    """Render the onboarding-first home page.

    Args:
        config: Application configuration.
        i18n: Translation helper.
        library_root: Configured library path.
    """
    content = get_onboarding_content(i18n.locale, library_root)
    content["status_lines"][1] = f"Web UI: http://localhost:{config.web_port}"

    with st.spinner(i18n.t("messages.scanning")):
        pdf_list = scan_library(library_root, config.recursive_scan)

    stats = get_stats(pdf_list)
    readable_count = stats["readable_count"]
    unreadable_count = stats["unreadable_count"]
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
    papers_path = library_root / "papers"
    papers_count = len(list(papers_path.rglob("*.pdf"))) if papers_path.exists() else 0
    needs_ocr_path = library_root / "needs_ocr"
    needs_ocr_count = len(list(needs_ocr_path.rglob("*.pdf"))) if needs_ocr_path.exists() else 0
    markdown_papers_path = library_root / "markdown" / "papers"
    markdown_count = len(list(markdown_papers_path.rglob("*.md"))) if markdown_papers_path.exists() else 0
    analyses_path = Path.home() / ".armarius" / "analyses"
    analyses_count = len(list(analyses_path.rglob("*.md"))) if analyses_path.exists() else 0
    synthesis_path = library_root / "synthesis"
    synthesis_count = len(list(synthesis_path.rglob("*.md"))) if synthesis_path.exists() else 0

    st.caption(content["badge"])
    st.header("Dashboard" if i18n.locale != "zh-TW" else "儀表板")
    st.write(
        "Workflow-first summary of your library, intake queue, and knowledge outputs."
        if i18n.locale != "zh-TW"
        else "先看目前文獻庫工作流狀態、收件佇列，以及知識產出進度。"
    )

    metric1, metric2, metric3, metric4 = st.columns(4)
    with metric1:
        st.metric("PDFs", stats["total_count"])
    with metric2:
        st.metric("可讀" if i18n.locale == "zh-TW" else "Readable", readable_count)
    with metric3:
        st.metric("不可讀" if i18n.locale == "zh-TW" else "Unreadable", unreadable_count)
    with metric4:
        st.metric("Size", f"{stats['total_size_mb']:.1f} MB")

    summary_col, setup_col = st.columns([2, 1])
    with summary_col:
        with st.container(border=True):
            st.markdown("**Library snapshot**" if i18n.locale != "zh-TW" else "**文獻庫摘要**")
            st.write(
                f"{stats['total_count']} PDFs · {readable_count} readable · {unreadable_count} unreadable"
                if i18n.locale != "zh-TW"
                else f"共 {stats['total_count']} 份 PDF，其中 {readable_count} 份可讀、{unreadable_count} 份不可讀"
            )
    with setup_col:
        with st.container(border=True):
            st.markdown("**Current workflow**" if i18n.locale != "zh-TW" else "**目前工作流**")
            st.write(
                f"{workflow_name} · {workflow_status.name.lower()}"
                if i18n.locale != "zh-TW"
                else f"{workflow_name} · {workflow_status.name.lower()}"
            )

    workflow_label_map = {
        LibraryStatus.UNINITIALIZED: "Uninitialized" if i18n.locale != "zh-TW" else "未初始化",
        LibraryStatus.INITIALIZED: "Initialized" if i18n.locale != "zh-TW" else "已初始化",
        LibraryStatus.OUTDATED: "Outdated" if i18n.locale != "zh-TW" else "版本過舊",
    }
    queue_data = [
            {
                "Stage": "Library workflow" if i18n.locale != "zh-TW" else "文獻庫工作流",
                "Status": workflow_label_map.get(
                    workflow_status,
                    "Unknown" if i18n.locale != "zh-TW" else "未知",
                ),
                "Count": str(workflow_name),
            },
            {
                "Stage": "Inbox" if i18n.locale != "zh-TW" else "收件匣",
                "Status": "Pending" if inbox_count else ("Empty" if i18n.locale != "zh-TW" else "目前為空"),
                "Count": str(inbox_count),
            },
            {
                "Stage": "Cataloged papers" if i18n.locale != "zh-TW" else "已編目論文",
                "Status": "Available" if papers_count else ("Not yet" if i18n.locale != "zh-TW" else "尚未建立"),
                "Count": str(papers_count),
            },
            {
                "Stage": "Needs OCR" if i18n.locale != "zh-TW" else "待 OCR",
                "Status": "Attention" if needs_ocr_count else ("Clear" if i18n.locale != "zh-TW" else "正常"),
                "Count": str(needs_ocr_count),
            },
            {
                "Stage": "Markdown notes" if i18n.locale != "zh-TW" else "Markdown 筆記",
                "Status": "Ready" if markdown_count else ("Missing" if i18n.locale != "zh-TW" else "尚未產生"),
                "Count": str(markdown_count),
            },
            {
                "Stage": "Analyses" if i18n.locale != "zh-TW" else "分析卡",
                "Status": "Ready" if analyses_count else ("Pending" if i18n.locale != "zh-TW" else "尚未產生"),
                "Count": str(analyses_count),
            },
            {
                "Stage": "Synthesis" if i18n.locale != "zh-TW" else "匯總輸出",
                "Status": "Ready" if synthesis_count else ("Pending" if i18n.locale != "zh-TW" else "尚未產生"),
                "Count": str(synthesis_count),
            },
        ]

    st.subheader("Quick actions" if i18n.locale != "zh-TW" else "快速操作")
    quick_columns = st.columns(4)
    workbench_cards = [
            {
                "emoji": "📥",
                "title": "Inbox" if i18n.locale != "zh-TW" else "收件匣",
                "body": (
                    f"{inbox_count} PDFs waiting in {inbox_path.name}."
                    if i18n.locale != "zh-TW"
                    else f"{inbox_path.name} 目前有 {inbox_count} 份 PDF 等待處理。"
                ),
                "hint": "Drop new PDFs here first." if i18n.locale != "zh-TW" else "先把新 PDF 丟到這裡。",
            },
            {
                "emoji": "🗂️",
                "title": "Catalog" if i18n.locale != "zh-TW" else "編目",
                "body": (
                    f"{papers_count} papers organized; {needs_ocr_count} need attention."
                    if i18n.locale != "zh-TW"
                    else f"已整理 {papers_count} 份；另有 {needs_ocr_count} 份待 OCR 或檢查。"
                ),
                "hint": "Use the Library page's catalog room." if i18n.locale != "zh-TW" else "到 Library 頁面的目錄室操作。",
            },
            {
                "emoji": "🎼",
                "title": "Analysis" if i18n.locale != "zh-TW" else "分析",
                "body": (
                    f"{analyses_count} analysis cards generated so far."
                    if i18n.locale != "zh-TW"
                    else f"目前已產生 {analyses_count} 張分析卡。"
                ),
                "hint": "Open the dedicated Paradigm Analysis page." if i18n.locale != "zh-TW" else "前往獨立的派典分析頁面。",
            },
            {
                "emoji": "🎭",
                "title": "Synthesis" if i18n.locale != "zh-TW" else "匯總",
                "body": (
                    f"{synthesis_count} synthesis outputs are available."
                    if i18n.locale != "zh-TW"
                    else f"目前有 {synthesis_count} 份匯總輸出可用。"
                ),
                "hint": "Open the dedicated Concerto Synthesis page."
                if i18n.locale != "zh-TW"
                else "前往獨立的協奏匯總頁面。",
            },
        ]
    for column, card in zip(quick_columns, workbench_cards):
        with column:
            with st.container(border=True):
                st.markdown(f"### {card['emoji']} {card['title']}")
                st.write(card["body"])
                st.caption(card["hint"])
                button_label = "Open" if i18n.locale != "zh-TW" else "前往"
                if st.button(
                    f"{button_label} {card['title']}",
                    key=f"workbench-{card['title']}",
                    width="stretch",
                ):
                    target_map = {
                        "Inbox": "statistics",
                        "收件匣": "statistics",
                        "Catalog": "catalog",
                        "編目": "catalog",
                        "Analysis": "paradigm_analysis",
                        "分析": "paradigm_analysis",
                        "Synthesis": "concerto_synthesis",
                        "匯總": "concerto_synthesis",
                    }
                    target = target_map[card["title"]]
                    if target in {"intake", "statistics", "catalog"}:
                        st.session_state["page"] = "library"
                        st.session_state["dashboard_target_room"] = target
                    else:
                        st.session_state["page"] = target
                    st.rerun()

    attention_title = "Needs attention" if i18n.locale != "zh-TW" else "目前要注意"
    st.subheader(attention_title)
    attention_items = []
    if workflow_status != LibraryStatus.INITIALIZED:
        attention_items.append(
            "Library workflow needs initialization or migration."
            if i18n.locale != "zh-TW"
            else "文獻庫工作流需要初始化或升級。"
        )
    if inbox_count:
        attention_items.append(
            f"Inbox still has {inbox_count} PDFs waiting."
            if i18n.locale != "zh-TW"
            else f"收件匣目前還有 {inbox_count} 份 PDF 等待處理。"
        )
    if needs_ocr_count:
        attention_items.append(
            f"{needs_ocr_count} PDFs still need OCR or cleanup."
            if i18n.locale != "zh-TW"
            else f"還有 {needs_ocr_count} 份 PDF 需要 OCR 或整理。"
        )
    if not attention_items:
        st.success("Everything looks healthy." if i18n.locale != "zh-TW" else "目前狀態良好。")
    else:
        for item in attention_items:
            with st.container(border=True):
                st.markdown("**Action**" if i18n.locale != "zh-TW" else "**注意事項**")
                st.write(item)

    status_title = "Recent library files" if i18n.locale != "zh-TW" else "最近文獻"
    db = ArmariusDatabase()
    intake_service = IntakeService(db, PDFProcessor(), library_root)
    recent_blobs = intake_service.list_recent_blobs(limit=10)

    intake_title = "Intake pipeline" if i18n.locale != "zh-TW" else "收件流程"
    st.subheader(intake_title)
    intake_col1, intake_col2 = st.columns([2, 1])
    with intake_col1:
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
        else:
            st.info("No intake records yet." if i18n.locale != "zh-TW" else "目前還沒有收件紀錄。")
    with intake_col2:
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

    st.subheader(status_title)
    if not pdf_list:
        st.warning(
            "No PDFs found in the configured folder yet."
            if i18n.locale != "zh-TW"
            else "目前設定資料夾還沒有找到 PDF。"
        )
    else:
        latest_files = sorted(pdf_list, key=lambda pdf: pdf.modified_time, reverse=True)[:5]
        table_data = [
            {
                "File": pdf.filename,
                "Pages": pdf.page_count if pdf.page_count else "N/A",
                "Status": (
                    "可讀" if i18n.locale == "zh-TW" else "Readable"
                ) if pdf.is_readable else (
                    "不可讀" if i18n.locale == "zh-TW" else "Unreadable"
                ),
            }
            for pdf in latest_files
        ]
        st.dataframe(table_data, width="stretch", hide_index=True)

    with st.expander("Workflow details" if i18n.locale != "zh-TW" else "工作流細節", expanded=False):
        st.dataframe(queue_data, width="stretch", hide_index=True)

    with st.expander("Setup and rooms" if i18n.locale != "zh-TW" else "設定與房間", expanded=False):
        setup_title = "Setup summary" if i18n.locale != "zh-TW" else "設定摘要"
        st.markdown(f"### {setup_title}")
        for line in content["status_lines"]:
            st.code(line, language="text")

        room_title = "Armarius rooms" if i18n.locale != "zh-TW" else "Armarius 房間"
        st.markdown(f"### {room_title}")
        room_lines = [
            "Library: scan, statistics, catalog, paradigm, synthesis"
            if i18n.locale != "zh-TW"
            else "Library：掃描、統計、編目、派典分析、協奏匯總",
            "Tutorial: usage guidance and prompts"
            if i18n.locale != "zh-TW"
            else "Tutorial：使用導引與提示詞",
            "Catalog Assistant: catalog templates and organization help"
            if i18n.locale != "zh-TW"
            else "編目助手：catalog 範本與組織方式說明",
        ]
        for line in room_lines:
            st.markdown(f"- {line}")

    next_title = "Next actions" if i18n.locale != "zh-TW" else "下一步"
    st.subheader(next_title)
    for tip in content["tips"]:
        st.markdown(f"- {tip}")

    if not pdf_list:
        guide_label = "Quick start" if i18n.locale != "zh-TW" else "快速開始"
        with st.expander(guide_label, expanded=True):
            for step in content["steps"]:
                st.markdown(f"**{step['title']}**")
                st.write(step["body"])
                st.code(step["code"], language="bash")

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
        intake_states = ["accepted", "quarantine", "needs_ocr", "rejected"]
        selected_states = st.multiselect(
            "States" if i18n.locale != "zh-TW" else "狀態",
            options=intake_states,
            default=["accepted", "quarantine", "needs_ocr"],
        )
        recent_blobs = intake_service.list_recent_blobs(limit=50, states=selected_states or None)
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
                st.json(detail)
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


def pick_page(i18n: I18n) -> str:
    """Render sidebar page navigation and return the selected page id.

    Args:
        i18n: Translation helper.

    Returns:
        Selected page key.
    """
    sections = [
        (
            "Dashboard" if i18n.locale != "zh-TW" else "儀表板",
            [("dashboard", "儀表板" if i18n.locale == "zh-TW" else "Dashboard")],
        ),
        (
            "Workflow" if i18n.locale != "zh-TW" else "工作流",
            [
                ("library", i18n.t("tabs.library")),
                ("paradigm_analysis", "派典分析" if i18n.locale == "zh-TW" else "Paradigm Analysis"),
                ("concerto_synthesis", "協奏匯總" if i18n.locale == "zh-TW" else "Concerto Synthesis"),
            ],
        ),
        (
            "Help" if i18n.locale != "zh-TW" else "輔助",
            [
                ("tutorial", i18n.t("tabs.tutorial")),
                ("catalog_assistant", i18n.t("tabs.catalog_assistant")),
            ],
        ),
    ]
    current = st.session_state.get("page", "dashboard")
    page_ids = [page_id for _, pages in sections for page_id, _ in pages]
    if current not in page_ids:
        current = "dashboard"
    for section_title, pages in sections:
        st.sidebar.caption(section_title)
        for page_id, label in pages:
            active = current == page_id
            if st.sidebar.button(
                ("● " if active else "") + label,
                key=f"page-{page_id}",
                width="stretch",
                type="primary" if active else "secondary",
            ):
                st.session_state["page"] = page_id
                return page_id
        st.sidebar.markdown("")
    current_labels = {page_id: label for _, pages in sections for page_id, label in pages}
    st.sidebar.info(
        (
            f"Current page: {current_labels[current]}"
            if i18n.locale != "zh-TW"
            else f"目前頁面：{current_labels[current]}"
        )
    )
    st.session_state["page"] = current
    return current


def render_paradigm_analysis_page(i18n: I18n) -> None:
    """Render the dedicated paradigm analysis page."""
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
                st.info(i18n.t("rooms.guide.phase1_notice"))


def render_concerto_synthesis_page(i18n: I18n) -> None:
    """Render the dedicated concerto synthesis page."""
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
            st.info(i18n.t("rooms.guide.phase1_notice"))


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

    # Sidebar: Settings, language selector, and theme selector
    with st.sidebar:
        st.header(i18n.t("sidebar.settings_header"))
        # Library path configuration - simple and safe
        st.subheader(i18n.t("sidebar.library_config_header") if i18n.t("sidebar.library_config_header") != "sidebar.library_config_header" else "📁 圖書館設定")
        
        # Current library path display
        st.caption(f"📍 {i18n.t('sidebar.current_library') if i18n.t('sidebar.current_library') != 'sidebar.current_library' else '當前圖書館'}: {library_root}")
        
        # Path input
        new_library_path = st.text_input(
            i18n.t("sidebar.path_input_label") if i18n.t("sidebar.path_input_label") != "sidebar.path_input_label" else "📂 輸入新路徑",
            value=str(library_root),
            help=i18n.t("sidebar.path_input_help") if i18n.t("sidebar.path_input_help") != "sidebar.path_input_help" else "輸入完整路徑，支援 ~ 符號。例如：~/Documents/papers",
            key="library_path_input",
        )
        
        # Quick paths - smaller buttons with custom CSS
        st.markdown("""<style>
        div[data-testid="column"] button {
            font-size: 0.85rem !important;
            padding: 0.25rem 0.5rem !important;
            white-space: nowrap !important;
        }
        </style>""", unsafe_allow_html=True)
        
        st.caption("🔗 " + (i18n.t("sidebar.quick_paths") if i18n.t("sidebar.quick_paths") != "sidebar.quick_paths" else "快速選擇"))
        col1, col2, col3, col4 = st.columns(4)
        
        from pathlib import Path as PathLib
        import platform
        
        # Column 1: Default path (priority)
        with col1:
            default_lib = config.get("library.default_path")
            if default_lib:
                default_path = PathLib(default_lib).expanduser()
                if st.button("⭐", width="stretch", help=i18n.t("sidebar.default") if i18n.t("sidebar.default") != "sidebar.default" else f"預設: {default_path.name}"):
                    try:
                        if default_path.exists():
                            config.set("library.root_path", str(default_path))
                            config.save()
                            st.session_state.update_success = str(default_path)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.session_state.update_error = "❌ 路徑不存在"
                    except Exception as e:
                        st.session_state.update_error = f"❌ {str(e)}"
        
        # Column 2: Desktop (OS-aware)
        with col2:
            # Determine desktop path based on OS
            system = platform.system()
            if system == "Darwin":  # macOS
                desktop_path = PathLib.home() / "Desktop"
            elif system == "Windows":
                desktop_path = PathLib.home() / "Desktop"
            else:  # Linux and others
                desktop_path = PathLib.home() / "Desktop"
            
            if st.button("🖥️", width="stretch", help=i18n.t("sidebar.desktop") if i18n.t("sidebar.desktop") != "sidebar.desktop" else "桌面"):
                try:
                    if desktop_path.exists():
                        config.set("library.root_path", str(desktop_path))
                        config.save()
                        st.session_state.update_success = str(desktop_path)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.session_state.update_error = "❌ 路徑不存在"
                except Exception as e:
                    st.session_state.update_error = f"❌ {str(e)}"
        
        # Column 3: Documents
        with col3:
            if st.button("📝", width="stretch", help=i18n.t("sidebar.documents") if i18n.t("sidebar.documents") != "sidebar.documents" else "文件"):
                try:
                    docs_path = PathLib.home() / "Documents"
                    if docs_path.exists():
                        config.set("library.root_path", str(docs_path))
                        config.save()
                        st.session_state.update_success = str(docs_path)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.session_state.update_error = "❌ 路徑不存在"
                except Exception as e:
                    st.session_state.update_error = f"❌ {str(e)}"
        
        # Column 4: Downloads
        with col4:
            if st.button("📥", width="stretch", help=i18n.t("sidebar.downloads") if i18n.t("sidebar.downloads") != "sidebar.downloads" else "下載"):
                try:
                    downloads_path = PathLib.home() / "Downloads"
                    if downloads_path.exists():
                        config.set("library.root_path", str(downloads_path))
                        config.save()
                        st.session_state.update_success = str(downloads_path)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.session_state.update_error = "❌ 路徑不存在"
                except Exception as e:
                    st.session_state.update_error = f"❌ {str(e)}"
        
        # Display update messages
        if "update_success" in st.session_state:
            st.success(f"✅ {st.session_state.update_success}")
            del st.session_state.update_success
        if "update_error" in st.session_state:
            st.error(st.session_state.update_error)
            del st.session_state.update_error
        # Update button
        if st.button("✅ " + (i18n.t("sidebar.update_path") if i18n.t("sidebar.update_path") != "sidebar.update_path" else "更新路徑"), width="stretch", type="primary"):
            new_path = PathLib(new_library_path).expanduser()
            
            if new_path.exists() and new_path.is_dir():
                config.set("library.root_path", str(new_path))
                config.save()
                st.success(i18n.t("messages.library_updated") if i18n.t("messages.library_updated") != "messages.library_updated" else f"✅ 圖書館路徑已更新！")
                st.cache_data.clear()
                st.rerun()
            elif not new_path.exists():
                st.error(i18n.t("errors.path_not_exist") if i18n.t("errors.path_not_exist") != "errors.path_not_exist" else f"❌ 路徑不存在：{new_path}")
            else:
                st.error(i18n.t("errors.not_directory") if i18n.t("errors.not_directory") != "errors.not_directory" else f"❌ 不是資料夾：{new_path}")
        
        st.text(f"{i18n.t('sidebar.recursive_label')}: {config.recursive_scan}")
        st.divider()

        if st.button(i18n.t("sidebar.refresh_button"), width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        
        st.caption(f"{i18n.t('sidebar.config_label')}: {config.config_path}")
        
        st.divider()
        
        # Common sidebar settings (language, theme, version)
        render_sidebar_settings(config, i18n)

    page = pick_page(i18n)

    if page == "dashboard":
        render_home_page(config, i18n, library_root)
    elif page == "library":
        render_library_page(config, i18n, library_root)
    elif page == "paradigm_analysis":
        render_paradigm_analysis_page(i18n)
    elif page == "concerto_synthesis":
        render_concerto_synthesis_page(i18n)
    elif page == "tutorial":
        render_tutorial(i18n)
    elif page == "catalog_assistant":
        render_catalog_assistant(config, i18n)


def render_tutorial(i18n):
    """Render the tutorial page with i18n support."""
    st.title(i18n.t("tutorial.title"))
    
    # Welcome section
    st.header(i18n.t("tutorial.welcome"))
    st.write(i18n.t("tutorial.welcome_desc"))
    
    st.divider()
    
    # Quick Start
    st.header(i18n.t("tutorial.quick_start.title"))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader(i18n.t("tutorial.quick_start.step1_title"))
        st.write(i18n.t("tutorial.quick_start.step1_desc"))
    
    with col2:
        st.subheader(i18n.t("tutorial.quick_start.step2_title"))
        st.write(i18n.t("tutorial.quick_start.step2_desc"))
    
    with col3:
        st.subheader(i18n.t("tutorial.quick_start.step3_title"))
        st.write(i18n.t("tutorial.quick_start.step3_desc"))
    
    st.divider()
    
    # Features
    st.header(i18n.t("tutorial.features.title"))
    
    st.subheader(i18n.t("tutorial.features.library_title"))
    st.markdown(i18n.t("tutorial.features.library_desc"))
    
    st.subheader(i18n.t("tutorial.features.search_title"))
    st.write(i18n.t("tutorial.features.search_desc"))
    
    st.subheader(i18n.t("tutorial.features.stats_title"))
    st.write(i18n.t("tutorial.features.stats_desc"))
    
    st.divider()
    
    # Quick Buttons
    st.header(i18n.t("tutorial.quick_buttons.title"))
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{i18n.t('tutorial.quick_buttons.default_title')}**")
        st.write(i18n.t("tutorial.quick_buttons.default_desc"))
        
        st.markdown(f"**{i18n.t('tutorial.quick_buttons.documents_title')}**")
        st.write(i18n.t("tutorial.quick_buttons.documents_desc"))
    
    with col2:
        st.markdown(f"**{i18n.t('tutorial.quick_buttons.desktop_title')}**")
        st.write(i18n.t("tutorial.quick_buttons.desktop_desc"))
        
        st.markdown(f"**{i18n.t('tutorial.quick_buttons.downloads_title')}**")
        st.write(i18n.t("tutorial.quick_buttons.downloads_desc"))
    
    st.divider()
    
    # Tips
    st.header(i18n.t("tutorial.tips.title"))
    
    # Tip 1: Let AI configure
    with st.expander(i18n.t("tutorial.tips.tip1_title"), expanded=True):
        st.write(i18n.t("tutorial.tips.tip1_desc"))
        st.code(i18n.t("tutorial.tips.tip1_prompt"), language="text")
    
    # Tip 2: Organize PDFs
    with st.expander(i18n.t("tutorial.tips.tip2_title")):
        st.write(i18n.t("tutorial.tips.tip2_desc"))
        st.code(i18n.t("tutorial.tips.tip2_prompt"), language="text")
    
    # Tip 3: Quick customization
    with st.expander(i18n.t("tutorial.tips.tip3_title")):
        st.write(i18n.t("tutorial.tips.tip3_desc"))
    
    st.divider()
    
    # Coming Soon
    st.header(i18n.t("tutorial.coming_soon.title"))
    st.markdown(i18n.t("tutorial.coming_soon.phase1"))
    st.markdown(i18n.t("tutorial.coming_soon.phase2"))
    st.markdown(i18n.t("tutorial.coming_soon.phase3"))
    
    st.divider()
    
    # Feedback
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
