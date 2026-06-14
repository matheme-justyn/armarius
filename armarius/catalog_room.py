"""Catalog Room - File browsing and cataloging operations.

Displays files in _input directory and provides cataloging controls.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from armarius.config import ArmariusConfig
from armarius.database import ArmariusDatabase
from armarius.catalog_loader import CatalogLoader
from armarius.ui_common import I18n


def render_catalog_room(
    config: ArmariusConfig, db: ArmariusDatabase, library_root: Path, workflow, status, i18n: I18n
):
    """Render catalog room with file browser and cataloging controls."""

    st.subheader(i18n.t("workflow.status_title"))
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        from armarius.workflow import LibraryStatus

        if status == LibraryStatus.UNINITIALIZED:
            st.warning(i18n.t("workflow.status_uninitialized"))
        elif status == LibraryStatus.INITIALIZED:
            st.success(i18n.t("workflow.status_initialized"))
        elif status == LibraryStatus.OUTDATED:
            st.warning(i18n.t("workflow.status_outdated"))

    with col2:
        st.metric(i18n.t("workflow.version_current"), workflow.get_library_version() or "N/A")

    with col3:
        st.metric(i18n.t("workflow.version_expected"), workflow.get_expected_version())
    
    if status != LibraryStatus.INITIALIZED:
        return
    st.divider()
    
    input_folder = workflow.get_input_folder()
    st.info(i18n.t("workflow.input_folder"))
    st.code(str(input_folder), language="bash")
    
    try:
        input_files = list(input_folder.glob("*.pdf")) if input_folder.exists() else []
    except Exception as e:
        st.error(f"Error reading input folder: {e}")
        return
    
    if not input_files:
        st.warning(i18n.t("catalog_room.no_files_in_input"))
        return
    
    st.divider()
    
    try:
        project_root = Path(__file__).parent.parent
        catalogs_dir = Path.home() / ".armarius" / "catalogs"
        project_templates = project_root / "catalogs"
        
        loader = CatalogLoader(catalogs_dir=catalogs_dir, project_templates=project_templates)
        catalogs = loader.list_catalogs()
    except Exception as e:
        st.error(f"Error loading catalogs: {e}")
        import traceback
        st.code(traceback.format_exc())
        return
    
    if not catalogs:
        st.warning(i18n.t("catalog_operations.no_configs_warning"))
        return

    current_method = config.get("library.catalog.method", "flat")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(f"**{i18n.t('catalog_room.files_in_input')}**: {len(input_files)}")

    with col2:
        catalog_options = {f"{cat['name']} ({cat['method']})": cat for cat in catalogs}
        catalog_names = list(catalog_options.keys())

        try:
            default_idx = next(
                i
                for i, name in enumerate(catalog_names)
                if catalog_options[name]["method"] == current_method
            )
        except StopIteration:
            default_idx = 0

        selected_catalog_name = st.selectbox(
            i18n.t("catalog_room.select_catalog_method"),
            options=catalog_names,
            index=default_idx,
            key="catalog_selector",
            label_visibility="collapsed",
        )
        selected_catalog = catalog_options[selected_catalog_name]
        selected_method = selected_catalog["method"]

    catalog_config = loader.load_catalog(selected_catalog["file_path"])

    df_data = []
    for pdf_file in input_files:
        old_location = str(pdf_file.relative_to(library_root))

        new_location = calculate_new_location(
            pdf_file, library_root, selected_method, catalog_config
        )

        df_data.append(
            {
                i18n.t("catalog_room.table.filename"): pdf_file.name,
                i18n.t("catalog_room.table.extension"): pdf_file.suffix,
                i18n.t("catalog_room.table.status"): i18n.t("catalog_room.status.pending"),
                i18n.t("catalog_room.table.old_location"): old_location,
                i18n.t("catalog_room.table.new_location"): new_location,
            }
        )

    df = pd.DataFrame(df_data)

    st.dataframe(
        df, width="stretch", hide_index=True, height=min(400, len(df_data) * 35 + 38)
    )

    st.divider()

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button(
            i18n.t("catalog_room.button.new_catalog"),
            type="primary",
            width="stretch",
            help=i18n.t("catalog_room.button.new_catalog_help"),
        ):
            st.session_state.catalog_action = "new"
            st.session_state.selected_method = selected_method
            st.session_state.catalog_config = catalog_config

    with col2:
        if st.button(
            i18n.t("catalog_room.button.recatalog"),
            width="stretch",
            help=i18n.t("catalog_room.button.recatalog_help"),
        ):
            st.session_state.catalog_action = "recatalog"
            st.session_state.selected_method = selected_method
            st.session_state.catalog_config = catalog_config

    if "catalog_action" in st.session_state:
        action = st.session_state.catalog_action
        method = st.session_state.selected_method

        if action == "new":
            execute_new_catalog(
                input_files, library_root, db, method, st.session_state.catalog_config, i18n
            )
        elif action == "recatalog":
            execute_recatalog(
                library_root, db, method, st.session_state.catalog_config, config, i18n
            )

        del st.session_state.catalog_action
        del st.session_state.selected_method
        del st.session_state.catalog_config
        st.rerun()


def calculate_new_location(
    pdf_file: Path, library_root: Path, method: str, catalog_config: Dict[str, Any]
) -> str:
    """Calculate new location based on catalog method."""

    if method == "flat":
        return f"{pdf_file.name}"

    elif method == "by_year":
        return f"YYYY/{pdf_file.name} (待提取年份)"

    elif method == "by_venue":
        return f"Venue/{pdf_file.name} (待提取期刊)"

    elif method == "custom":
        categories = catalog_config.get("categories", [])
        if categories:
            first_cat = categories[0].get("name", "Uncategorized")
            return f"{first_cat}/{pdf_file.name}"
        return f"Uncategorized/{pdf_file.name}"

    return f"{pdf_file.name}"


def execute_new_catalog(
    input_files: List[Path],
    library_root: Path,
    db: ArmariusDatabase,
    method: str,
    catalog_config: Dict[str, Any],
    i18n: I18n,
):
    """Execute cataloging for _input files only."""
    from armarius.cataloging import CatalogingService

    with st.spinner(i18n.t("catalog_room.processing.new_catalog")):
        cataloger = CatalogingService(library_root, db)

        success_count = 0
        error_count = 0

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, pdf_file in enumerate(input_files):
            status_text.text(f"{i18n.t('catalog_room.processing.current')}: {pdf_file.name}")

            try:
                result = cataloger.ingest_paper(
                    pdf_path=pdf_file, catalog_method=method, enable_network_lookup=True
                )

                if result.success:
                    success_count += 1
                else:
                    error_count += 1

            except Exception as e:
                error_count += 1
                st.error(f"{pdf_file.name}: {str(e)}")

            progress_bar.progress((idx + 1) / len(input_files))

        progress_bar.empty()
        status_text.empty()

        st.success(
            i18n.t("catalog_room.result.new_catalog_complete").format(
                success=success_count, error=error_count
            )
        )


def execute_recatalog(
    library_root: Path,
    db: ArmariusDatabase,
    method: str,
    catalog_config: Dict[str, Any],
    config: ArmariusConfig,
    i18n: I18n,
):
    """Execute recatalog for all non-underscore directories."""
    from armarius.cataloging import CatalogingService

    confirm = st.warning(i18n.t("catalog_room.confirm.recatalog_warning"))

    col1, col2 = st.columns(2)

    with col1:
        if st.button(i18n.t("catalog_room.confirm.yes"), type="primary"):
            with st.spinner(i18n.t("catalog_room.processing.recatalog")):
                cataloger = CatalogingService(library_root, db)

                result = cataloger.recatalog_library(new_method=method)

                if result["success"]:
                    st.success(
                        i18n.t("catalog_room.result.recatalog_complete").format(
                            moved=result["moved_count"], skipped=result["skipped_count"]
                        )
                    )

                    config.set("library.catalog.method", method)
                    config.save()
                else:
                    st.error(i18n.t("catalog_operations.recatalog.failed"))

    with col2:
        if st.button(i18n.t("catalog_room.confirm.no")):
            st.info(i18n.t("catalog_room.confirm.cancelled"))
