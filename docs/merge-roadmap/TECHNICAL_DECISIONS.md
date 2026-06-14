# Capsa 技術決策記錄（Technical Decision Record）

> 記錄日期：2026-06-11
> 
> 本文件記錄 Capsa 項目從 PDF 知識管理系統演進為 LLM-Wiki 系統的所有關鍵技術決策。

---

## 目錄

1. [專案願景與定位](#專案願景與定位)
2. [架構演進決策](#架構演進決策)
3. [PDF 處理技術棧](#pdf-處理技術棧)
4. [資料庫選型](#資料庫選型)
5. [Wiki 系統設計](#wiki-系統設計)
6. [依賴關係與模組化](#依賴關係與模組化)
7. [實作優先級](#實作優先級)

---

## 專案願景與定位

### 核心問題
傳統 RAG 系統的根本問題：**每次查詢都重新發現知識，沒有記憶累積**。

### Capsa 的解決方案
受 Andrej Karpathy 的 LLM-Wiki 模式啟發，Capsa 採用三層架構：

```
raw/ (PDF 檔案，不可變)
  ↓
wiki/ (LLM 維護的知識層，持續成長)
  ↓
查詢介面 (CLI + Web UI + MCP)
```

**核心差異化**：
- ✅ **學術 PDF 專精**：精確到 bounding box 的引用
- ✅ **視覺證據**：每個引用都有截圖為證
- ✅ **知識編譯一次，持續維護**：不是 RAG 的「用過即丟」
- ✅ **Multi-Agent 協作**：專門的 Agent 負責不同任務

---

## 架構演進決策

### 決策 1：拆分 PDF 工具為獨立模組

**決定**：將 PDF 解析和截圖功能獨立為 `pdfkit` 模組，未來可獨立成套件。

**理由**：
1. 關注點分離：PDF 治理 ≠ 知識管理
2. 可重用性：其他項目（閱讀器、註解工具、引用管理器）也可以用
3. 獨立演進：pdfkit 和 capsa 可以分開開發

**實作策略**：
- **Phase 1（現在）**：在同一個 repo 裡模組化
  ```
  capsa/
  ├── src/
  │   ├── pdfkit/        # 邏輯獨立（未來可拆）
  │   └── capsa/         # 主要邏輯
  ```
- **Phase 2（未來）**：當 pdfkit 穩定後，拆成獨立 repo

---

### 決策 2：不依賴 Obsidian

**決定**：Capsa 自己提供 Web UI，不依賴 Obsidian 作為前端。

**理由**：
1. 降低用戶門檻：不用裝 Obsidian
2. 功能可控：可以針對學術場景定制 UI
3. 部署簡單：一個指令就能啟動

**實作方案**：
- FastAPI + Jinja2 模板（簡單）
- 或 FastAPI + Alpine.js（更好的互動）
- D3.js 實現簡單的 Graph View

**保留彈性**：
- Wiki 仍然是 markdown 檔案
- 用戶可以自己用 Obsidian 或任何編輯器打開

---

### 決策 3：Wiki 和 Qdrant 的雙層索引架構

**決定**：Wiki 作為「快取層」，Qdrant 保留完整檢索能力。

**架構**：
```
查詢請求
  ↓
先查 wiki/index.md（輕量，幾 KB）
  ↓
  ├─ Wiki 有相關頁面且足夠 → 直接返回（省 Qdrant 查詢）
  │
  └─ Wiki 沒有或不足
      ↓
      查 Qdrant（向量搜尋）
      ↓
      SummarizeAgent 合成
      ↓
      WikiAgent 判斷是否存檔
      ├─ 值得 → 寫入 wiki/
      └─ 不值得 → 只返回
```

**判斷「Wiki 是否足夠」的邏輯**：
```python
class WikiQueryDecider:
    """
    1. 概念性問題（"什麼是 transformer"）→ Wiki 足夠
    2. 精確引用（"論文 X 第 3 頁說了什麼"）→ 必須查 Qdrant
    3. 比較性問題且 Wiki 有相關比較頁 → Wiki 足夠
    4. 涉及新論文（Wiki 裡沒有）→ 必須查 Qdrant
    """
```

---

## PDF 處理技術棧

### 決策 4：PDF 入庫的四大需求

**需求清單**：
1. ✅ **重新命名**：有 DOI 用 DOI 命名，沒有用 hash
2. ✅ **資料庫管制**：追蹤位置、狀態、版本、hash 防篡改
3. ✅ **Markdown 化**：包含表格和圖片
4. ✅ **截圖提取**：關鍵圖片額外輸出為資產

---

### 決策 5：Markdown 轉換工具選型

**經過搜尋和比較後的決定**：**Marker + PyMuPDF（混合方案）**

#### **候選工具評估（2026 年最新）**：

| 工具 | Stars | 優點 | 缺點 | 評分 |
|------|-------|------|------|------|
| **Marker** | 19K+ | 速度快、多格式、可選 LLM 增強 | GPL 3.0、需 GPU（可選） | ⭐⭐⭐⭐⭐ |
| **MinerU** | 67K+ | 表格最強、公式轉 LaTeX、中文優秀 | 設定複雜、需 GPU | ⭐⭐⭐⭐ |
| **Docling** | 20K+ | IBM 出品、RAG 整合好 | 需 CUDA | ⭐⭐⭐⭐ |
| PyMuPDF4LLM | 2K+ | 最快、不需 GPU | 不支援 OCR、表格弱 | ⭐⭐⭐ |
| OpenDataLoader | 新 | Benchmark #1、Apache 2.0 | 生態小 | ⭐⭐⭐ |

#### **最終方案：智能路由**

```python
class SmartConverter:
    def convert(self, pdf_path: str):
        pdf_type = self.detect_pdf_type(pdf_path)
        
        if pdf_type == "digital_text_only":
            return PyMuPDF4LLM.convert(pdf_path)  # 最快
        elif pdf_type == "academic_with_formulas":
            return MinerU.convert(pdf_path)       # 公式最好（可選）
        else:
            return Marker.convert(pdf_path)       # 通用場景
```

**決策理由**：
1. **Marker 為主力**：平衡速度與質量，不強制 GPU
2. **PyMuPDF 快速路徑**：純文字 PDF 用最快的方式處理
3. **MinerU 可選**：學術場景需要時才啟用（避免複雜依賴）

**依賴安裝策略**：
```toml
[project.dependencies]
marker-pdf = ">=1.0.0"       # 必須
pymupdf = ">=1.24.0"         # 必須

[project.optional-dependencies]
academic = [
    "magic-pdf[full]"        # MinerU（可選）
]
```

---

### 決策 6：DOI 管理和元數據

**決定**：用 CrossRef API 自動提取 DOI 和元數據。

**實作**：
```python
class DOIManager:
    def extract_doi_from_pdf(self, pdf_path: str) -> str | None:
        """從 PDF 前 2 頁提取 DOI"""
        # 正則：10\.\d{4,}/[^\s]+
    
    def get_metadata_from_doi(self, doi: str) -> dict:
        """從 CrossRef 獲取：title, authors, year, journal"""
    
    def rename_pdf_by_doi(self, pdf_path: str) -> Path:
        """
        格式：doi-10.1234-5678.pdf
        沒 DOI：no-doi-{hash}.pdf
        """
```

**為什麼選 CrossRef**：
- ✅ 免費 API
- ✅ 涵蓋範圍廣
- ✅ 元數據完整（標題、作者、年份、期刊）

---

### 決策 7：截圖策略

**決定**：混合模式（重要的嵌入，次要的按需生成）。

```python
class CitationManager:
    def decide_screenshot_mode(self, citation):
        if citation.is_key_definition():
            return "embed"      # 重要定義 → 嵌入截圖到 wiki
        elif citation.is_supporting_evidence():
            return "on_demand"  # 佐證資料 → 按需生成
        else:
            return "link_only"  # 次要引用 → 只存連結
```

**Wiki 範例**：
```markdown
## Key Definition (嵌入截圖)
![](screenshot1.png)

## Supporting Evidence (按需生成)
[📸 View Citation](capsa://cite/paper1/p3/bbox1)
```

**啟發式規則（圖片重要性）**：
```python
def identify_key_figures(self, figures: list):
    for fig in figures:
        score = 0
        if fig["width"] > 500 and fig["height"] > 400:
            score += 2  # 大圖更重要
        if fig["size_kb"] > 100:
            score += 1  # 複雜圖更重要
        if fig["page"] <= 3:
            score += 1  # 在前幾頁
        
        if score >= 2:
            key_figures.append(fig)
```

---

## 資料庫選型

### 決策 8：使用 DuckDB（不是 SQLite，不是 PostgreSQL）

**決定**：用 **DuckDB** 管理 PDF 元數據和結構化資料。

**為什麼選 DuckDB**：

| 特性 | DuckDB | SQLite | PostgreSQL |
|------|--------|--------|------------|
| **分析查詢速度** | ⭐⭐⭐⭐⭐（快 10-100x） | ⭐⭐ | ⭐⭐⭐⭐ |
| **嵌入式** | ✅ 單一檔案 | ✅ | ❌ 需要 server |
| **JSON 支援** | ✅ 原生 | ⚠️ 有限 | ✅ |
| **結構化類型** | ✅ STRUCT, LIST | ❌ | ✅ |
| **Parquet 原生** | ✅ | ❌ | ❌ |
| **配置複雜度** | ⭐（零配置） | ⭐ | ⭐⭐⭐⭐ |
| **多人協作** | ⚠️ 有限 | ❌ | ✅ |

**DuckDB 的殺手級功能**：
```python
# 1. 原生 JSON
conn.execute("SELECT authors->>'$.name' FROM pdfs")

# 2. 結構化類型（bbox 是 STRUCT）
conn.execute("""
    SELECT * FROM citations
    WHERE bbox.x0 > 100 AND bbox.y0 > 200
""")

# 3. 直接返回 DataFrame
df = conn.execute("SELECT year, COUNT(*) FROM pdfs GROUP BY year").df()

# 4. 分析查詢飛快（比 SQLite 快 10-100 倍）
conn.execute("SELECT * FROM pdfs WHERE year BETWEEN 2020 AND 2024")
```

**Schema 設計**：
```sql
CREATE TABLE pdfs (
    id INTEGER PRIMARY KEY,
    doi TEXT UNIQUE,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL UNIQUE,  -- SHA256 防篡改
    title TEXT,
    authors JSON,                     -- DuckDB 原生 JSON
    year INTEGER,
    journal TEXT,
    status TEXT DEFAULT 'indexed',
    version INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    markdown_path TEXT,
    assets_dir TEXT
);

CREATE TABLE citations (
    id INTEGER PRIMARY KEY,
    pdf_id INTEGER,
    page INTEGER,
    bbox STRUCT(x0 FLOAT, y0 FLOAT, x1 FLOAT, y1 FLOAT),  -- 結構化！
    text TEXT,
    screenshot_path TEXT
);
```

**與 Qdrant 的分工**：
- **DuckDB**：結構化資料（metadata, citations, bbox）
- **Qdrant**：向量（embeddings for semantic search）

**什麼時候才用 PostgreSQL**：
- ❌ 不需要：單機使用、個人知識庫
- ✅ 需要：多人協作、需要 pgvector、已有 PostgreSQL 基礎設施

---

## Wiki 系統設計

### 決策 9：Wiki 目錄結構

```
wiki/
├── papers/                      # 每篇論文一個摘要頁
│   ├── attention-is-all-you-need.md
│   └── bert.md
│
├── concepts/                    # 跨論文的概念整理
│   ├── attention-mechanism.md
│   └── transformer-architecture.md
│
├── comparisons/                 # 比較分析（查詢生成的）
│   ├── transformer-vs-lstm.md
│   └── bert-vs-gpt.md
│
├── researchers/                 # 人物頁（可選）
│   └── vaswani-ashish.md
│
├── timelines/                   # 時間線（可選）
│   └── attention-mechanism-history.md
│
├── _assets/                     # 截圖和圖片
│   ├── screenshots/
│   └── diagrams/
│
├── _templates/                  # Wiki 頁面模板
│   ├── concept.md
│   ├── paper.md
│   └── comparison.md
│
├── index.md                     # Wiki 總索引
├── log.md                       # 操作歷史
└── graph.json                   # 頁面連結關係（可選）
```

---

### 決策 10：Wiki Frontmatter 設計

```yaml
---
# wiki/concepts/transformer-architecture.md

type: concept                    # concept | comparison | paper_summary
created: 2026-06-11
updated: 2026-06-11
confidence: high                 # low | medium | high（根據來源數量）

# 學術特有欄位
sources:
  - paper: attention-is-all-you-need
    pages: [3, 5, 8]
    relevance: primary           # primary | supporting | contradictory
  - paper: bert
    pages: [2]
    relevance: supporting

cited_by:                        # 哪些 wiki 頁面引用了這頁
  - transformer-vs-lstm
  - attention-mechanisms-overview

keywords:
  - attention mechanism
  - self-attention

# 狀態追蹤
needs_update: false              # LintAgent 會標記
contradictions: []
missing_citations: []
---
```

**為什麼這樣設計**：
1. **可追溯性**：每個說法都有來源
2. **信心度**：根據來源數量評估
3. **自動維護**：LintAgent 可以根據 metadata 判斷哪些頁面需要更新
4. **Dataview 查詢**（如果用 Obsidian）

---

### 決策 11：什麼樣的內容該寫進 Wiki

**一定要存的**：
```python
MUST_SAVE = [
    "multi_paper_summary",     # 跨論文摘要
    "comparison",              # 比較分析
    "contradiction_found",     # 發現矛盾
    "concept_definition",      # 概念定義（被問過 2 次以上）
    "research_timeline",       # 研究脈絡時間線
]
```

**不該存的**：
```python
DONT_SAVE = [
    "single_chunk_lookup",     # 單純查某一段文字
    "yes_no_question",         # 簡單的是非題
    "formatting_request",      # "幫我改格式"
    "translation",             # 翻譯請求
]
```

**判斷邏輯**：
```python
class WikiSaveDecider:
    def should_save(self, query: str, result: dict) -> tuple[bool, str]:
        """
        Returns: (是否存檔, 存檔類型)
        
        Criteria:
        - Synthesizes multiple sources → YES (type: synthesis)
        - Resolves contradiction → YES (type: contradiction)
        - Defines important concept → YES (type: concept)
        - Simple fact lookup → NO
        """
```

---

### 決策 12：Index.md 和 Log.md 的格式

#### **Index.md（內容導向）**：
```markdown
# Capsa Wiki Index

Last updated: 2026-06-11 10:30

## Quick Stats
- Total papers: 47
- Concepts: 23
- Comparisons: 8

## Papers (by topic)
- [[attention-is-all-you-need]] • *Transformer* • 12 refs • ⭐ foundational
- [[bert]] • *Bidirectional pretraining* • 8 refs • 2018

## Concepts (alphabetical)
- [[attention-mechanism]] • 15 papers • 🔄 updated 2026-06-11
- [[transformer-architecture]] • 12 papers • ⭐ well-documented

## Needs Attention
- [[positional-encoding]] • ⚠️ Contradiction found
```

**設計原則**：
- 足夠豐富：LLM 能快速定位
- 足夠精簡：能塞進 context

#### **Log.md（時間導向）**：
```markdown
# Capsa Wiki Log

## [2026-06-11 10:30] ingest | attention-is-all-you-need.pdf
- Created: [[attention-is-all-you-need]]
- Updated: [[attention-mechanism]], [[transformer-architecture]]
- Added: 15 citations with screenshots
- Status: ✅ Success

## [2026-06-11 10:15] query | "Compare transformer and LSTM"
- Read: [[transformer-architecture]], [[lstm]]
- Created: [[transformer-vs-lstm]]
- Status: ✅ Saved to wiki
```

**用途**：
1. 人類瀏覽：了解 wiki 怎麼演變的
2. Agent 參考：避免重複工作
3. Unix 工具解析：`grep "^## \[" wiki/log.md | tail -5`

---

### 決策 13：LintAgent 的具體邏輯

```python
class LintAgent:
    def run_health_check(self) -> LintReport:
        """
        定期執行（例如每天或每 10 次 ingest）
        """
        issues = []
        
        # 1. 找矛盾：兩個 wiki 頁面對同一概念有不同定義
        contradictions = self.find_contradictions()
        
        # 2. 找孤島：沒有任何 [[inbound links]] 的頁面
        orphans = self.find_orphan_pages()
        
        # 3. 找缺失：常被提到但沒有獨立頁面的概念
        missing_concepts = self.find_missing_concept_pages()
        
        # 4. 找過時：有新論文但相關概念頁沒更新
        stale_pages = self.find_stale_pages()
        
        # 5. 找低信心：只有 1 個來源的概念定義
        low_confidence = self.find_low_confidence_pages()
        
        # 6. 建議新方向
        suggestions = self.suggest_new_research()
        
        return LintReport(...)
```

**執行時機**：定期（每天）或每 10 次 ingest。

---

## 依賴關係與模組化

### 決策 14：最終的系統架構

```
┌─────────────────────────────────────────────────┐
│              pdfkit (未來獨立)                    │
│  PDF → chunks + bbox → screenshots              │
└─────────────────────────────────────────────────┘
                    ↓ (API)
┌─────────────────────────────────────────────────┐
│                   Capsa                         │
│                                                 │
│  ┌──────────────┐    ┌──────────────┐         │
│  │  Storage     │    │   Agents     │         │
│  │  (Qdrant)    │←──→│ (Query/Wiki) │         │
│  │  (DuckDB)    │    │              │         │
│  └──────────────┘    └──────────────┘         │
│         ↓                    ↓                  │
│  ┌──────────────────────────────────┐         │
│  │         Wiki Layer               │         │
│  │  wiki/*.md (markdown files)      │         │
│  └──────────────────────────────────┘         │
│         ↓                    ↓                  │
│  ┌──────────────┐    ┌──────────────┐         │
│  │     CLI      │    │   Web UI     │         │
│  │ (index/query)│    │  (FastAPI)   │         │
│  └──────────────┘    └──────────────┘         │
└─────────────────────────────────────────────────┘
```

### 決策 15：目錄結構

```
capsa/
├── src/
│   ├── pdfkit/                 # 未來獨立（現在在同一個 repo）
│   │   ├── __init__.py
│   │   ├── doi_manager.py     # DOI 提取 + CrossRef
│   │   ├── database.py        # DuckDB 管理
│   │   ├── converter.py       # Marker + PyMuPDF
│   │   └── screenshot.py      # 截圖提取
│   │
│   └── capsa/
│       ├── storage/
│       │   ├── embedder.py
│       │   ├── vector_store.py  # Qdrant
│       │   └── indexer.py
│       ├── agents/
│       │   ├── query.py
│       │   ├── summarize.py
│       │   ├── citation.py
│       │   └── wiki.py         # 新增：WikiAgent
│       ├── wiki/               # Wiki 核心邏輯
│       │   ├── index.py        # Index 維護
│       │   ├── lint.py         # LintAgent
│       │   └── templates/
│       ├── web/                # Web UI
│       │   ├── app.py          # FastAPI
│       │   ├── routes/
│       │   └── templates/
│       ├── mcp/                # MCP Server（保留）
│       └── cli.py
│
├── wiki/                       # Wiki 內容（git tracked）
│   ├── papers/
│   ├── concepts/
│   ├── comparisons/
│   ├── _assets/
│   ├── index.md
│   └── log.md
│
├── data/
│   └── pdfs.duckdb            # DuckDB 資料庫
│
├── docs/
│   ├── TECHNICAL_DECISIONS.md  # 本文件
│   └── API.md
│
├── tests/
├── pyproject.toml
└── README.md
```

---

### 決策 16：依賴管理

```toml
# pyproject.toml

[project]
name = "capsa"
version = "0.2.0"
dependencies = [
    # 核心
    "duckdb>=1.0.0",              # 資料庫
    "qdrant-client>=1.7.0",       # 向量存儲
    "sentence-transformers>=2.2.0", # Embeddings
    
    # PDF 處理
    "marker-pdf>=1.0.0",          # 主力 PDF 轉換
    "pymupdf>=1.24.0",            # 快速路徑 + 截圖
    "requests>=2.31.0",           # CrossRef API
    
    # Web UI
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
    "jinja2>=3.1.0",
    
    # CLI
    "click>=8.1.0",
    "rich>=13.7.0",
]

[project.optional-dependencies]
# 學術場景（可選）
academic = [
    "magic-pdf[full]>=0.7.0",    # MinerU
]

# MCP Server
mcp = [
    "mcp>=0.1.0",
]

# 開發工具
dev = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
]

# 全部安裝
all = [
    "capsa[academic,mcp,dev]",
]
```

---

## 實作優先級

### Phase 1：基礎架構重構（Week 1）

**目標**：模組化現有代碼 + 加入 WikiAgent

#### Day 1-2：模組化 pdfkit
```bash
# 把 PDF 相關邏輯隔離
src/capsa/pdfkit/
├── __init__.py
├── doi_manager.py
├── database.py        # DuckDB
├── converter.py       # Marker + PyMuPDF
└── screenshot.py
```

**驗證**：
```python
from capsa.pdfkit import PDFKit

kit = PDFKit()
result = kit.ingest("test.pdf")
# 應該返回：pdf_id, doi, markdown_path, figures
```

#### Day 3-4：實作 WikiAgent
```python
# src/capsa/agents/wiki_agent.py

class WikiAgent:
    def create_page(self, content, metadata):
        """創建 wiki 頁面（含 frontmatter）"""
    
    def update_index(self):
        """更新 index.md"""
    
    def append_log(self, event):
        """寫入 log.md"""
    
    def should_save(self, query, result):
        """判斷是否值得存成 wiki"""
```

**驗證**：
```bash
capsa query "What is transformer"
# → 產生 wiki/concepts/transformer.md
# → 更新 wiki/index.md
# → 寫入 wiki/log.md
```

#### Day 5-7：基礎 Web UI
```python
# src/capsa/web/app.py

@app.get("/")
def index():
    """顯示 wiki/index.md"""

@app.get("/wiki/{page}")
def view_page(page: str):
    """顯示單一頁面（markdown → HTML）"""

@app.get("/search")
def search(q: str):
    """全文搜尋"""
```

**驗證**：
```bash
capsa serve
# 瀏覽器打開 http://localhost:8080
# 可以看到 wiki 內容、點擊 [[links]]、搜尋
```

---

### Phase 2：完善功能（Week 2）

#### Day 8-10：截圖整合
- Wiki 頁面能顯示嵌入的截圖
- 實作混合模式（重要的嵌入、次要的按需）
- 截圖路徑管理

#### Day 11-12：搜尋和導航
- 全文搜尋高亮
- 麵包屑導航
- 按類別過濾

#### Day 13-14：Graph View（簡單版）
- 用 D3.js 畫關係圖
- 可以點擊跳轉

---

### Phase 3：進階功能（Week 3+）

#### LintAgent 實作
- 找矛盾邏輯
- 找孤島邏輯
- 健康報告生成

#### MinerU 整合（可選）
- 只在學術場景啟用
- 與 Marker 的路由邏輯

#### 多語言支援
- Markdown 完成後統一翻譯為英文和繁體中文

---

## 關鍵設計原則

### 1. 漸進式增強
- Phase 1 可用（基本功能）
- Phase 2 好用（完善體驗）
- Phase 3 強大（進階功能）

### 2. 模組化優先
- pdfkit 獨立於 capsa
- Wiki 獨立於 RAG
- Web UI 可選（CLI 也能用）

### 3. 開源優先
- 核心功能用開源工具（Marker, DuckDB）
- 商業工具可選（MinerU 學術場景）
- 避免鎖定（Wiki 是 markdown，可以用任何工具打開）

### 4. 效能考量
- 簡單 PDF → 快速路徑（PyMuPDF）
- 複雜 PDF → Marker
- 學術 PDF → MinerU（可選）

### 5. 用戶體驗
- 零配置：`pip install capsa && capsa serve`
- 不依賴外部工具（Obsidian 可選）
- 提供多種介面（CLI, Web, MCP）

---

## 未來考量

### 可能的擴展方向
1. **團隊協作**：多人共編 wiki（需要 PostgreSQL + 權限管理）
2. **雲端同步**：Wiki 備份到 S3/GitHub
3. **更多格式**：支援 Word、PPT、Excel
4. **AI 對話**：直接在 Web UI 裡問問題
5. **匯出功能**：Wiki → PDF / HTML / Notion

### 不做的事情（至少現階段）
- ❌ 不做通用文件管理（專注學術 PDF）
- ❌ 不做社交功能（不是 Notion/Roam）
- ❌ 不做複雜權限系統（個人/小團隊用）
- ❌ 不做移動端 App（Web UI 響應式即可）

---

## 附錄：參考資料

### 關鍵文獻
1. [Andrej Karpathy's LLM Wiki Pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
2. [Marker GitHub](https://github.com/datalab-to/marker)
3. [MinerU GitHub](https://github.com/opendatalab/MinerU)
4. [Docling GitHub](https://github.com/docling-project/docling)
5. [DuckDB Documentation](https://duckdb.org/docs/)

### Benchmark 報告
1. [Best Open-Source PDF-to-Markdown Tools 2026](https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026)
2. [PDF Processing Frameworks: RAG Accuracy Study](https://www.machinebrief.com/news/pdf-processing-frameworks-the-linchpin-of-rag-accuracy-a83x)
3. [Docling vs Marker for RAG Pipelines](https://docs.bswen.com/blog/2026-04-16-docling-vs-marker-document-parsing/)

---

## 變更歷史

| 日期 | 版本 | 變更說明 |
|------|------|----------|
| 2026-06-11 | 1.0 | 初始版本，記錄所有核心技術決策 |

---

**本文件是活文件，隨專案演進持續更新。**
