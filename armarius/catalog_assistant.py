"""Catalog Assistant - Tutorial and configuration helper.

This module provides educational content and guidance for configuring
catalog templates, not the actual cataloging operations.
"""

import streamlit as st
from pathlib import Path
from armarius.config import CardexConfig
from armarius.catalog_loader import CatalogLoader
from armarius.ui_common import I18n


def render_catalog_assistant(config: CardexConfig, i18n: I18n):
    """Render catalog assistant tutorial page.

    Args:
        config: Application configuration
        i18n: Internationalization helper
    """
    st.header("📚 編目助手 | Catalog Assistant")
    st.markdown("---")

    locale = i18n.locale

    if locale == "zh-TW":
        render_tutorial_zh_tw()
    else:
        render_tutorial_en_us()

    render_catalog_browser(config)


def render_tutorial_zh_tw():
    """Render tutorial in Traditional Chinese."""
    st.subheader("❓ 什麼是編目助手？")

    st.markdown(
        """
    ### 📖 編目助手功能

    編目助手幫助你：
    - **理解編目系統**：了解不同編目方法的優缺點
    - **配置 Catalog YAML**：學習如何創建和修改 catalog 配置檔
    - **管理編目模板**：瀏覽和選擇適合你的編目策略

    **注意**：實際的編目操作（ingest、recatalog）在主頁面的「目錄室」區塊執行。

    ---

    ### 🗂️ 什麼是 Catalog 配置？

    Catalog 配置檔（`.catalog.yaml`）定義了你的文獻庫如何組織：

    **4 種編目方法**：
    1. **flat** - 扁平結構：所有文件在同一目錄
       ```
       library/
       ├─ paper1.pdf
       ├─ paper2.pdf
       └─ paper3.pdf
       ```

    2. **by_year** - 按年份分類：依出版年份組織
       ```
       library/
       ├─ 2023/
       │  ├─ paper1.pdf
       │  └─ paper2.pdf
       └─ 2024/
          └─ paper3.pdf
       ```

    3. **by_venue** - 按期刊/會議分類：依發表場所組織
       ```
       library/
       ├─ Nature/
       │  └─ paper1.pdf
       ├─ ICML/
       │  └─ paper2.pdf
       └─ NeurIPS/
          └─ paper3.pdf
       ```

    4. **custom** - 自訂分類：依你定義的類別組織
       ```
       library/
       ├─ ML_Theory/
       │  └─ paper1.pdf
       ├─ NLP_Applications/
       │  └─ paper2.pdf
       └─ Computer_Vision/
          └─ paper3.pdf
       ```

    ---

    ### 📝 如何創建 Catalog 配置？

    1. **複製範本**：從 `catalogs/` 目錄複製一個範例檔案
    2. **修改配置**：編輯 YAML 檔案，調整編目方法和命名規則
    3. **存放位置**：
       - 專案範本：`<project>/catalogs/*.catalog.yaml`（給所有人用）
       - 個人配置：`~/.cardex/catalogs/*.catalog.yaml`（你自己的）

    **範例配置結構**：
    ```yaml
    name: "My Custom Catalog"
    description: "Organize by research topics"
    version: "1.0"

    method: "custom"  # flat | by_year | by_venue | custom

    categories:
      - name: "ML Theory"
        description: "Machine Learning Theory papers"
        keywords: ["theory", "foundations"]

    naming:
      primary: "doi"     # Use DOI as filename
      fallback: "title"  # Use title if DOI not found

    special_dirs:
      inbox: "_input"              # 收件箱
      duplicates: "_duplicates"    # 重複文件
      no_metadata: "_no_metadata"  # 無法提取元資料
    ```

    ---

    ### 🔧 配置檔案位置

    - **專案範本**（範例檔）：`<project_root>/catalogs/`
      - `example.catalog.yaml` - 完整範例（含註解）
      - `flat.catalog.yaml` - 扁平結構範本
      - `by_year.catalog.yaml` - 按年份範本
      - `by_venue.catalog.yaml` - 按期刊/會議範本

    - **個人配置**（你的設定）：`~/.cardex/catalogs/`
      - 複製範本後修改，存在這裡
      - 不會被 Git 追蹤，適合個人化設定

    ---

    ### 💡 使用建議

    **初學者**：
    - 先使用 `flat` 或 `by_year`，簡單直觀
    - 等文獻量大後再考慮 `by_venue` 或 `custom`

    **進階使用者**：
    - 使用 `by_venue` 追蹤研究領域動態
    - 使用 `custom` 建立個人化知識分類

    **切換編目方法**：
    - 在主頁面「目錄室」中可以切換編目方法
    - 系統會自動重新組織你的文獻庫

    ---

    ### ⚠️ 重要提醒

    - `_input/` 目錄永遠被保留，不會被移動
    - 切換編目方法時，系統會重新組織所有文件
    - 建議在切換前備份你的文獻庫
    """
    )


def render_tutorial_en_us():
    """Render tutorial in English."""
    st.subheader("❓ What is Catalog Assistant?")

    st.markdown(
        """
    ### 📖 Features

    Catalog Assistant helps you:
    - **Understand the catalog system**: Learn pros/cons of different methods
    - **Configure Catalog YAML**: Learn how to create and modify catalog configs
    - **Manage catalog templates**: Browse and choose strategies that fit you

    **Note**: Actual cataloging operations (ingest, recatalog) happen in the Library Room on the main page.

    ---

    ### 🗂️ What is a Catalog Configuration?

    A catalog config file (`.catalog.yaml`) defines how your library is organized:

    **4 Catalog Methods**:
    1. **flat** - Flat structure: All files in one directory
    2. **by_year** - By publication year
    3. **by_venue** - By journal/conference
    4. **custom** - By user-defined categories

    ---

    ### 📝 How to Create a Catalog Config?

    1. **Copy a template**: From `catalogs/` directory
    2. **Modify config**: Edit YAML file, adjust method and naming rules
    3. **File locations**:
       - Project templates: `<project>/catalogs/*.catalog.yaml` (shared)
       - Personal configs: `~/.cardex/catalogs/*.catalog.yaml` (your own)

    **Example configuration**:
    ```yaml
    name: "My Custom Catalog"
    method: "custom"
    categories:
      - name: "ML Theory"
        keywords: ["theory", "foundations"]
    naming:
      primary: "doi"
      fallback: "title"
    ```

    ---

    ### 🔧 File Locations

    - **Project templates**: `<project_root>/catalogs/`
      - `example.catalog.yaml` - Full example with comments
      - `flat.catalog.yaml`, `by_year.catalog.yaml`, `by_venue.catalog.yaml`

    - **Personal configs**: `~/.cardex/catalogs/`
      - Copy and modify templates here
      - Not tracked by Git

    ---

    ### 💡 Usage Tips

    **Beginners**: Start with `flat` or `by_year`
    **Advanced**: Use `by_venue` or `custom` for sophisticated organization
    **Switching methods**: Done in Library Room - system reorganizes automatically
    """
    )


def render_catalog_browser(config: CardexConfig):
    """Render catalog template browser.

    Args:
        config: Application configuration
    """
    st.subheader("📂 可用的 Catalog 配置 | Available Catalog Configs")

    project_root = Path(__file__).parent.parent
    catalogs_dir = Path.home() / ".armarius" / "catalogs"
    project_templates = project_root / "catalogs"

    loader = CatalogLoader(catalogs_dir=catalogs_dir, project_templates=project_templates)

    catalogs = loader.list_catalogs()

    if not catalogs:
        st.info("沒有找到 catalog 配置檔。請從專案 `catalogs/` 目錄複製範例。")
        st.info("No catalog configs found. Copy examples from project `catalogs/` directory.")
        return

    for catalog in catalogs:
        source_badge = "🏠 User" if catalog["source"] == "user" else "📦 Template"

        with st.expander(f"{source_badge} {catalog['name']} ({catalog['method']})"):
            st.markdown(f"**Description**: {catalog['description']}")
            st.markdown(f"**Method**: `{catalog['method']}`")
            st.markdown(f"**File**: `{catalog['file_path']}`")

            full_config = loader.load_catalog(catalog["file_path"])
            if full_config:
                import yaml

                st.code(
                    yaml.dump(full_config, allow_unicode=True, sort_keys=False), language="yaml"
                )
