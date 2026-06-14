# Armarius

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](./VERSION)
[![License](https://img.shields.io/badge/license-TBD-yellow.svg)](./LICENSE)

[English](./README.md) | 繁體中文

> **學術知識管理系統** — 從 PDF 到結構化知識卡片的完整生命週期

Armarius 是一個完全可程式化的學術文獻管理系統，專為研究者設計。它不依賴任何 GUI 應用程式，所有資料儲存在開放格式（SQLite + Markdown），可透過自託管的 Web 服務視覺化。

> ⚠️ **前導版本**：本專案正在開發中（0.X 版本）。1.0.0 正式發佈前可能會有不相容的變更。

## 📇 關於命名

**Armarius** 是拉丁文，指中世紀修道院裡**掌管圖書室與繕寫室的人** — 負責看守 *armarium*（藏書櫃），為手抄本編目、監督抄寫、並借閱出借。

在搜尋引擎出現之前的漫長歲月裡，armarius 就是一切記錄知識的「人肉索引」：決定什麼值得保存、把它整理到能被找到、再將它從一個世代傳遞到下一個世代。那是耐心、細緻，而且常常不為人知的工作。

Armarius 向這個角色致敬，並在數位時代重新想像它 — AI 協助抄寫與編目，但研究者始終是那位決定「什麼才重要」的守護者。



---

- [什麼是 Armarius？](#什麼是-armarius)
- [核心特色](#核心特色)
- [快速開始](#快速開始)
- [建議工作流程](#建議工作流程)
- [文件](#文件)

---

## 什麼是 Armarius？

Armarius 將你的學術 PDF 收藏轉換成可查詢的知識庫：

- **自動 metadata 擷取** - 標題、作者、期刊、引用關係自動解析
- **多角度摘要** - 使用可插拔的「Skill」生成不同摘要（方法論、安全性、一般等）
- **證據分級** - 知道哪些論文有 Nature/Science 背書，哪些是 preprint
- **引用追蹤** - 看到你引用過但還沒讀的論文
- **AI 論證** - 從你的文獻庫生成有證據支持的論述

---

## ✨ 核心特色

### 🎯 設計理念

- **完全可程式化** - CLI 優先，不被 GUI 綁架
- **開放格式** - SQLite + Markdown（可移植、Git 友善）
- **自託管** - 你的資料永遠在你的機器上
- **編輯器無關** - 使用 VSCode、Obsidian 或任何 Markdown 編輯器

### 💡 Armarius 有什麼不同？

1. **Skill 系統** - 對同一篇論文生成多種觀點
   - 應用不同的分析視角（方法論、安全性、證據強度）
   - 透過 YAML 設定檔擴展

2. **證據分級** - 自動評估來源品質
   - Tier 1：Nature/Science/CORE A* 期刊 + RCT 方法論
   - 知道哪些主張有強證據支持

3. **Argue Engine** - 建構有證據支持的論述
   - 提出研究問題
   - AI 搜尋你的文獻庫並按證據強度排序
   - 取得帶有內聯引用的結構化論述

4. **引用警報** - 追蹤你接下來該讀什麼
   - 被引用多次但還沒在你文獻庫中的論文
   - 理解研究脈絡和學術網絡

---

## 🚀 快速開始

```bash
uv tool install --editable '.[web]'
armarius init
armarius serve
```

然後打開 `http://localhost:8501` 看 Web UI。

如果你比較習慣用虛擬環境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[web]'
```

---

## 🔄 建議工作流程

### 選項 1：VSCode + Foam（推薦）

1. **初始設定**：
   ```bash
   armarius init  # 設定文獻庫資料夾
   armarius serve # 在背景啟動 Web 服務
   ```

2. **日常工作流程**：
   - 將新 PDF 丟進 inbox 資料夾
   - Armarius 自動掃描並處理
   - 用 VSCode + Foam 擴充套件開啟 `markdown/papers/`
   - 做筆記、加標籤、用 `[[wikilinks]]` 連結論文
   - 需要引用圖或論證生成時使用 Web UI

3. **寫作模式**：
   - 在 Web UI 開啟 Argue Engine
   - 輸入你的論點陳述
   - 取得有證據支持的論述和引用
   - 匯出成 Markdown 後在 VSCode 繼續精修

### 選項 2：純 Web UI

- 啟動 `armarius serve`
- 透過 Web 介面上傳 PDF
- 在瀏覽器中閱讀摘要、探索引用圖、生成論述

### 選項 3：CLI 進階使用者

```bash
# 批次攝入
armarius ingest ~/Downloads/*.pdf

# 為所有論文生成摘要
armarius summarize --all --skills general,methodology

# 搜尋你的文獻庫
armarius search "transformer architecture"

# 匯出成 BibTeX
armarius export --format bibtex > library.bib
```

---

## 📖 文件

- **[PRD](./docs/PRD.md)** - 完整產品需求
- **[資料模型](./docs/data-model.md)** - 資料庫 schema 和檔案佈局
- **[技術棧](./docs/technology-stack.md)** - 為什麼選擇這些工具
- **[Phase 0 規格](./docs/phase-0-service-foundation.md)** - 當前開發階段

### 技術棧概覽

- **Backend**: Python + FastAPI
- **Frontend**: Streamlit (Phase 0-1) → React (Phase 2+)
- **Database**: SQLite + SQLAlchemy
- **AI/RAG**: LlamaIndex + LiteLLM（支援 OpenAI、Anthropic、Ollama）
- **Vector Store**: ChromaDB
- **PDF Processing**: PyMuPDF
- **CLI**: Click

詳細說明請見 [docs/technology-stack.md](./docs/technology-stack.md)。

---

## 🗓️ 開發狀態

**當前階段**：Phase 1 - Ingest Pipeline（建立在 Phase 0 基礎之上）

✅ **Phase 0 已完成**：
- 設定系統（`~/.armarius/config.yaml`、環境變數覆寫）
- PDF 掃描器含 metadata 擷取（檔案大小、頁數、可讀性）
- Streamlit Web UI 含資料庫瀏覽、搜尋、篩選
- CLI 指令（`armarius init`、`armarius serve`、`armarius scan`）
- i18n 支援（en-US、zh-TW）和主題切換
- SQLite 資料庫含完整 schema（papers、paradigms、analyses、syntheses）
- Docker/Podman 容器化含完整部署腳本
- Paradigm Analysis 系統（YAML-based、多視角分析）
- Concerto Synthesis 系統（針對不同受眾的輸出生成）

🛠️ **Phase 1 進行中**：
- 進階 PDF metadata 擷取（作者、標題、出處、DOI）
- 檔案重新命名和組織系統
- 傳統 Skill 系統（用於一般性摘要）

📋 **接下來**：
- Phase 2：引用圖和未讀通知
- Phase 3：Argue Engine（證據加權論證）
- Phase 4：進階 RAG 使用 LlamaIndex + ChromaDB

---

## 🤝 貢獻

本專案以作者自身需求為主要導向，但歡迎社群提交 issue 或討論功能建議。

如需貢獻程式碼，請：
1. Fork 本專案
2. 建立 feature branch (`git checkout -b feature/amazing-feature`)
3. Commit 你的變更（遵循 [AGENTS.md](./AGENTS.md) 中的規範）
4. Push 到你的 branch
5. 開啟 Pull Request

詳見 [CONTRIBUTING.md](./CONTRIBUTING.md)

---

## 📄 授權

授權方式待定（TBD）- 將選擇開源授權，詳見 [LICENSE](./LICENSE)

---

## 🙏 致謝

Armarius 靈感來源於：
- Zotero（文獻管理）
- Obsidian（知識連結）
- LlamaIndex（RAG 架構）
- 以及所有在學術研究中掙扎的研究者們 📚

---

**基於**: [my-vibe-scaffolding](https://github.com/matheme-justyn/my-vibe-scaffolding) v1.13.0

更多關於 README 撰寫的指引，請參考 [.template/docs/README_GUIDE.md](./.template/docs/README_GUIDE.md)
