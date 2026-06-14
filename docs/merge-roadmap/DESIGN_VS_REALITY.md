# 設計 vs 實作：差異分析

> **目的**：釐清設計文件（`TECHNICAL_DECISIONS.md`, `ADVANCED_FEATURES_DESIGN.md`）與現有程式碼的差異，幫助規劃後續開發策略

**文件版本**：2026-06-12
**程式碼版本**：v0.1.0

---

## TL;DR（關鍵發現）

| 層面 | 設計文件 | 實作現狀 | 差距評估 |
|------|---------|---------|---------|
| **PDF 處理** | Marker + PyMuPDF | 僅 PyMuPDF | ⚠️ 中等 |
| **資料庫** | DuckDB | 無（只有 Qdrant） | 🔴 重大 |
| **Wiki 系統** | 完整檔案結構 + 索引 | 不存在 | 🔴 重大 |
| **測試覆蓋** | 假設有完整測試 | 0 行測試 | 🔴 重大 |
| **進階功能** | 三大功能（可信度/Persona/文獻回顧） | 不存在 | 🔴 完全無 |

**結論**：設計文件描述的是「理想架構」，現有程式碼是「MVP 原型」。兩者差距約 **3-4 週的開發工作**。

---

## 第一部分：基礎架構差異

### 1. PDF 處理工具鏈

#### **設計文件的假設**

來源：`TECHNICAL_DECISIONS.md` - 決策 5

```yaml
主要工具: Marker (markdown 轉換)
  - 用途: 生成高品質 markdown（給 Wiki 系統用）
  - 特性: 保留 LaTeX、處理複雜版面、支援圖片提取
  
輔助工具: PyMuPDF (bounding box)
  - 用途: 精確座標提取（給引用系統用）
  - 特性: 快速、座標精準、截圖生成
  
整合策略:
  - Marker 負責 PDF → Markdown（Wiki 原料）
  - PyMuPDF 負責 bounding box + 截圖（Citation 原料）
  - 兩者互補，不重疊
```

#### **實作現狀**

來源：`src/capsa/parser/pdf_parser.py`, `pyproject.toml`

```python
# 只有 PyMuPDF
import fitz  # PyMuPDF

class PDFParser:
    def extract_text_with_bbox(self, page_num: int) -> List[TextChunk]:
        """只從 PDF 提取 text blocks + bounding boxes"""
        page = self.doc[page_num]
        text_dict = page.get_text("dict")
        # 直接用 block-level 切分，沒有 markdown 轉換
```

**依賴套件（pyproject.toml）**：
```toml
dependencies = [
    "pymupdf>=1.24.0",  # ✅ 有
    # "marker-pdf",      # ❌ 無
]
```

#### **差異分析**

| 功能 | 設計 | 實作 | 影響 |
|------|------|------|------|
| Markdown 轉換 | Marker 生成 | 無 | ❌ 無法生成結構化 markdown |
| LaTeX 公式保留 | Marker 支援 | 無 | ❌ 數學公式遺失 |
| 複雜表格處理 | Marker 優化 | PyMuPDF 基礎解析 | ⚠️ 表格可能錯亂 |
| Bounding box | PyMuPDF 提供 | PyMuPDF 提供 | ✅ 已實作 |
| 截圖生成 | PyMuPDF 提供 | PyMuPDF 提供 | ✅ 已實作 |

**結論**：
- ✅ **Citation 系統可用**（有 bbox + 截圖）
- ❌ **Wiki 系統無法建立**（缺 markdown 轉換）
- ⚠️ **內容品質受限**（LaTeX、表格處理差）

---

### 2. 資料庫架構

#### **設計文件的假設**

來源：`TECHNICAL_DECISIONS.md` - 決策 8, `ADVANCED_FEATURES_DESIGN.md` - 第 5 節

```yaml
DuckDB (主要資料庫):
  用途:
    - PDF 元數據管理（檔案、DOI、作者、期刊）
    - 可信度評分（journals, authors 表）
    - Persona 定義和點評記錄
    - 文獻回顧項目管理
  
  優勢:
    - 嵌入式（無需 server）
    - 分析查詢快（OLAP 優化）
    - 原生支援 JSON/struct types
    - 可直接查詢 parquet 檔案
  
  Schema 設計（11 個表）:
    核心表: pdfs, chunks, citations
    可信度: journals, authors, pdf_journal_link, pdf_author_link
    Persona: reader_personas, persona_reviews
    文獻回顧: literature_reviews, review_iterations

Qdrant (向量資料庫):
  用途:
    - 語義搜尋（embeddings）
    - 只存 chunks 的向量表示
  
  定位: 輔助搜尋層，檢查 Wiki 後才用
```

#### **實作現狀**

來源：`src/capsa/storage/`, README.md

```python
# 只有 Qdrant
from qdrant_client import QdrantClient

class VectorStore:
    def __init__(self, data_dir: Path = Path.home() / ".capsa" / "qdrant"):
        self.client = QdrantClient(path=str(data_dir))
        
    def add_chunk(self, chunk: TextChunk, embedding: List[float]) -> str:
        point = PointStruct(
            id=chunk_id,
            vector=embedding,
            payload={
                "text": chunk.text,
                "pdf_path": chunk.pdf_path,  # 字串，不是外鍵
                "page": chunk.bbox.page,
                "bbox": chunk.bbox.to_dict(),
            }
        )
```

**儲存位置**：
```
~/.capsa/
└── qdrant/          # Qdrant 向量資料庫
    ├── collection/
    └── meta.json
# 沒有 metadata.duckdb
# 沒有 wiki/ 目錄
```

#### **差異分析**

| 資料類型 | 設計（DuckDB） | 實作（Qdrant payload） | 影響 |
|---------|---------------|---------------------|------|
| PDF 元數據 | `pdfs` 表（title, authors, DOI） | 無 | ❌ 無法追蹤文件來源 |
| 期刊評級 | `journals` 表 | 無 | ❌ 可信度系統無法建立 |
| 作者資訊 | `authors` 表 | 無 | ❌ 作者追蹤不可行 |
| Chunk 結構化欄位 | 原生 struct types | JSON payload（扁平） | ⚠️ 查詢效能差 |
| 關聯查詢 | SQL JOIN | 只能靠 filter | ❌ 無法做複雜分析 |

**實際問題範例**：

```sql
-- 設計文件假設可以做這種查詢
SELECT p.title, AVG(j.impact_factor) 
FROM pdfs p
JOIN pdf_journal_link pjl ON p.id = pjl.pdf_id
JOIN journals j ON pjl.journal_id = j.id
GROUP BY p.title;

-- 但現實中只能這樣
results = vector_store.scroll(...)  # 拿全部
# 然後在 Python 裡手動過濾和聚合 🤦
```

**結論**：
- ❌ **無法實作進階功能**（可信度、Persona、文獻回顧）
- ❌ **無法做結構化查詢**（例如「找出所有 Nature 期刊的論文」）
- ⚠️ **擴展性差**（Qdrant payload 不適合複雜結構）

---

### 3. Wiki 系統

#### **設計文件的假設**

來源：`TECHNICAL_DECISIONS.md` - 決策 9-13

```yaml
Wiki 目錄結構:
  wiki/
    papers/              # 每篇論文一個 .md
      attention-2017.md
      bert-2018.md
    concepts/            # 概念詞條
      transformer.md
      self-attention.md
    comparisons/         # 跨文件比較
      attention-mechanisms.md
    reviews/             # 文獻綜述
      nlp-transformers-2024.md
    _index/              # 索引檔案
      by-author.md
      by-year.md
      by-topic.md
    _assets/             # 截圖、圖片
      attention-2017-fig1.png

Wiki Frontmatter (每個 .md 檔案):
  ---
  title: "Attention Is All You Need"
  type: paper | concept | comparison | review
  source: papers/attention-2017.pdf
  doi: 10.48550/arXiv.1706.03762
  authors: ["Vaswani et al."]
  year: 2017
  credibility_score: 95
  created: 2024-06-10
  updated: 2024-06-11
  tags: [transformer, nlp, attention]
  ---

Wiki 的作用:
  1. 知識快取層（減少 RAG overhead）
  2. 人類可讀的知識庫（可版本控制）
  3. 多視角內容整合（不只是檢索）
  4. 支援文獻回顧生成（從 wiki 組合）
```

#### **實作現狀**

```bash
# 專案根目錄沒有 wiki/
$ ls ~/capsa/
.git/  docs/  src/  tests/  README.md  pyproject.toml

# 也沒有任何 markdown 生成邏輯
$ grep -r "wiki" src/
# (no matches)
```

**結論**：
- ❌ **Wiki 系統完全不存在**
- ❌ **無法實作 Karpathy 的 LLM-Wiki 模式**
- ❌ **無法做知識複利（compounding knowledge）**

---

### 4. DOI 和元數據管理

#### **設計文件的假設**

來源：`TECHNICAL_DECISIONS.md` - 決策 6

```yaml
Ingest Pipeline (四步驟):
  1. DOI 提取和重命名
     - 從 PDF 元數據提取 DOI
     - 從 CrossRef API 拉取完整元數據
     - 重命名: "paper.pdf" → "attention-is-all-you-need-2017.pdf"
  
  2. 資料庫註冊
     - 插入 pdfs 表（title, authors, doi, journal, year）
     - Hash 校驗（防重複入庫）
  
  3. Markdown 轉換
     - Marker 生成 markdown
     - 存入 wiki/papers/
  
  4. 關鍵圖表提取
     - 識別重要圖片
     - 存入 wiki/_assets/
```

#### **實作現狀**

來源：`src/capsa/storage/indexer.py`, `src/capsa/parser/pdf_parser.py`

```python
class DocumentIndexer:
    def index_pdf(self, pdf_path: Path) -> int:
        # 1. 直接解析，不提取 DOI ❌
        chunks = self.parser.extract_all(pdf_path)
        
        # 2. 不查元數據 ❌
        # 3. 不重命名檔案 ❌
        
        # 4. 直接 embed + 存 Qdrant
        embeddings = self.embedder.embed_batch(texts)
        self.vector_store.add_chunks_batch(chunks, embeddings)
        
        return len(chunks)

class PDFParser:
    def get_metadata(self) -> dict:
        """只從 PDF 內部元數據讀取（不查 CrossRef）"""
        metadata = self.doc.metadata  # PyMuPDF 內建
        return {
            "title": metadata.get("title", ""),  # 常常是空的
            "author": metadata.get("author", ""), # 格式不統一
            # 沒有 DOI, journal, impact_factor
        }
```

**結論**：
- ❌ **無 DOI 管理**（無法做可信度評估）
- ❌ **無期刊識別**（無法偵測掠奪性期刊）
- ❌ **無作者追蹤**（無法計算 h-index）
- ⚠️ **檔名混亂**（使用者自己命名，不一致）

---

## 第二部分：進階功能差異

### 5. 可信度管理系統

#### **設計文件**

來源：`ADVANCED_FEATURES_DESIGN.md` - 第 2 節

```yaml
CredibilityAgent:
  功能:
    - 自動評估期刊（DOAJ, Beall's List, Impact Factor）
    - 追蹤作者（h-index, citation count）
    - 綜合評分（期刊 40% + 作者 30% + 論文 30%）
  
  資料模型:
    journals:
      - id, name, issn, impact_factor, is_predatory, doaj_indexed
    authors:
      - id, name, h_index, total_citations, affiliation
    pdf_journal_link:
      - pdf_id, journal_id
    pdf_author_link:
      - pdf_id, author_id, author_position
  
  CLI 指令:
    capsa assess paper.pdf           # 評估單篇
    capsa credibility list --flagged # 列出可疑論文
    capsa credibility update         # 更新期刊資料
```

#### **實作現狀**

```bash
# 無相關程式碼
$ find src/ -name "*credibility*" -o -name "*journal*" -o -name "*author*"
# (no matches)

# 無相關 CLI 指令
$ capsa --help
Commands:
  index   Index PDF files for semantic search
  query   Search across indexed PDFs
  status  Show indexing status
# (沒有 assess, credibility 等指令)
```

**結論**：❌ **完全未實作**

---

### 6. Reader Persona 系統

#### **設計文件**

來源：`ADVANCED_FEATURES_DESIGN.md` - 第 3 節

```yaml
ReviewAgent:
  功能:
    - 載入 Persona 定義（YAML）
    - 用不同視角點評論文
    - 批次處理（一次套用所有 persona）
  
  Persona 範例:
    personas/teacher.yaml:
      name: "教學者視角"
      focus_areas: [clarity, examples, pedagogy]
      evaluation_criteria:
        - 概念解釋是否清晰
        - 是否適合教學
        - 範例是否充足
  
  資料模型:
    reader_personas:
      - id, name, description, focus_areas, prompt_template
    persona_reviews:
      - id, pdf_id, persona_id, rating, review_text, created_at
  
  CLI 指令:
    capsa review paper.pdf --persona teacher
    capsa review paper.pdf --personas all
    capsa review-compare paper.pdf  # 比較不同視角
```

#### **實作現狀**

```bash
# 無相關程式碼
$ find src/ -name "*persona*" -o -name "*review*"
# (no matches)

# 無 personas/ 目錄
$ ls personas/
# (不存在)
```

**結論**：❌ **完全未實作**

---

### 7. 互動式文獻回顧生成

#### **設計文件**

來源：`ADVANCED_FEATURES_DESIGN.md` - 第 4 節

```yaml
LiteratureReviewAgent:
  功能:
    - 生成文獻回顧草稿
    - 識別研究 gaps
    - 推薦補充論文（Semantic Scholar API）
    - 支援迭代改進
  
  工作流程:
    1. 定義研究問題
    2. 從 Wiki 收集相關內容
    3. 生成大綱和草稿
    4. GapAnalysisAgent 識別缺口
    5. 推薦論文
    6. 用戶補充 → 更新草稿
  
  資料模型:
    literature_reviews:
      - id, title, research_question, status, current_version
    review_iterations:
      - id, review_id, version, content, gaps_identified, created_at
    review_feedback:
      - id, review_id, feedback_text, addressed
  
  CLI 指令:
    capsa review-create --title "..." --question "..."
    capsa review-gaps 1
    capsa review-iterate 1
```

#### **實作現狀**

```bash
# 無相關程式碼
$ find src/ -name "*literature*" -o -name "*gap*"
# (no matches)

# 現有的 agents 只有基礎功能
$ ls src/capsa/agents/
base.py  citation_agent.py  compare_agent.py  
orchestrator.py  query_agent.py  summarize_agent.py
# (沒有 credibility_agent, review_agent, literature_review_agent)
```

**結論**：❌ **完全未實作**

---

## 第三部分：測試和品質保證

### 8. 測試覆蓋率

#### **設計文件的假設**

來源：`TECHNICAL_DECISIONS.md` - Phase 1-3

```yaml
測試要求:
  - 單元測試: parser, embedder, vector_store
  - 整合測試: agent workflow
  - 端到端測試: CLI commands
  
  工具:
    - pytest
    - pytest-cov (覆蓋率報告)
    - 目標: 80%+ 覆蓋率
```

#### **實作現狀**

```bash
$ ls tests/
__init__.py  # 0 行

$ pytest
# (找不到任何測試)

$ wc -l tests/*.py
0 tests/__init__.py
```

**測試檔案數量**：0
**測試覆蓋率**：0%

**結論**：❌ **完全無測試**

---

### 9. 文件和範例

#### **設計文件的假設**

- 完整的 API 文件
- 使用範例（CLI + Python API）
- 架構圖和流程圖

#### **實作現狀**

✅ **有的文件**：
- `README.md`（基礎介紹 + 快速開始）
- `AGENTS.md`（Agent 架構說明）
- `PROJECT_SUMMARY.md`（專案摘要）

❌ **缺少的文件**：
- API 參考文件（docstring 不完整）
- 進階使用範例
- 疑難排解指南
- 貢獻指南

**結論**：⚠️ **基礎文件完整，但缺進階內容**

---

## 第四部分：工具和依賴

### 10. Python 依賴套件

| 套件 | 設計假設 | 實作現狀 | 備註 |
|------|---------|---------|------|
| **PDF 處理** | | | |
| `pymupdf` | ✅ 必需 | ✅ 已安裝 | 用於 bbox + 截圖 |
| `marker-pdf` | ✅ 必需 | ❌ 未安裝 | 設計要求用於 markdown 轉換 |
| **資料庫** | | | |
| `duckdb` | ✅ 必需 | ❌ 未安裝 | 設計核心，但現實中沒用 |
| `qdrant-client` | ✅ 必需 | ✅ 已安裝 | 向量搜尋 |
| **元數據** | | | |
| `crossref-commons` | ⚠️ 建議 | ❌ 未安裝 | DOI 查詢 |
| `scholarly` | ⚠️ 建議 | ❌ 未安裝 | Google Scholar API（h-index） |
| **PII 偵測** | | | |
| `presidio-analyzer` | ⚠️ 建議 | ❌ 未安裝 | 隱私保護 |
| **其他** | | | |
| `sentence-transformers` | ✅ 必需 | ✅ 已安裝 | Embedding |
| `pydantic` | ✅ 必需 | ✅ 已安裝 | 資料驗證 |
| `click` | ✅ 必需 | ✅ 已安裝 | CLI 框架 |
| `rich` | ✅ 必需 | ✅ 已安裝 | CLI 美化 |

**結論**：
- ✅ 基礎工具齊全（PyMuPDF, Qdrant, embeddings）
- ❌ 關鍵依賴缺失（Marker, DuckDB, CrossRef API）

---

## 第五部分：差距總結與規劃建議

### 差距矩陣

| 功能模組 | 設計完整度 | 實作進度 | 差距工時 | 優先級 |
|---------|-----------|---------|---------|-------|
| **基礎架構** | | | | |
| PDF 解析（PyMuPDF） | 100% | 90% | 0.5 天 | P0 |
| Markdown 轉換（Marker） | 100% | 0% | 2-3 天 | P2 |
| DuckDB 資料庫 | 100% | 0% | 3-4 天 | P1 |
| Wiki 檔案系統 | 100% | 0% | 2-3 天 | P2 |
| DOI 管理 | 100% | 0% | 1-2 天 | P1 |
| **進階功能** | | | | |
| 可信度系統 | 100% | 0% | 5-7 天 | P1 |
| Persona 系統 | 100% | 0% | 4-5 天 | P2 |
| 文獻回顧生成 | 100% | 0% | 7-10 天 | P3 |
| **品質保證** | | | | |
| 單元測試 | 100% | 0% | 3-4 天 | P1 |
| 整合測試 | 100% | 0% | 2-3 天 | P2 |
| 文件補完 | 100% | 50% | 2-3 天 | P2 |

**總計差距**：約 **34-48 天**（6-9 週）

---

### 三種可行的發展路徑

#### **路徑 A：漸進式增量（推薦）**

**目標**：在現有架構上，優先實作最小可行的可信度系統

**Phase 1A：輕量級可信度（1 週）**
```yaml
1. 新增 SQLite 資料庫（不是 DuckDB）:
   - 只建立 journals, authors, pdfs 三個核心表
   - 用標準庫 sqlite3（無需新依賴）

2. 實作基礎 CredibilityAgent:
   - 從 PDF 元數據提取作者、期刊
   - 對照 Beall's List（靜態 JSON 檔案）
   - 簡單評分邏輯（期刊可信度 0-100）

3. CLI 指令:
   - capsa assess <pdf>  # 評估單篇
   - capsa list-flagged  # 列出可疑論文

4. 不做的事:
   - ❌ 不查 CrossRef API（避免外部依賴）
   - ❌ 不查 h-index（避免複雜性）
   - ❌ 不建立 Wiki 系統
   - ❌ 不整合 Marker
```

**優勢**：
- ✅ 1 週內可完成
- ✅ 立即有實用價值（識別掠奪期刊）
- ✅ 不破壞現有程式碼
- ✅ 驗證核心概念（可信度評估）

**後續決策點**（Phase 1A 完成後再評估）：
- SQLite 是否夠用？還是需要升級到 DuckDB？
- 是否需要 Wiki 系統？還是資料庫就夠？
- 是否需要 Marker？還是 PyMuPDF 就夠？

---

#### **路徑 B：完整重構（高風險）**

**目標**：完全按照設計文件重構整個系統

**Phase 1：基礎架構重構（2 週）**
```yaml
1. 整合 Marker:
   - 安裝和配置 Marker
   - 改寫 PDFParser 同時支援 PyMuPDF 和 Marker
   - 測試 markdown 轉換品質

2. 建立 DuckDB 層:
   - 設計 schema（11 個表）
   - 實作 ORM 或 query builder
   - 遷移現有 Qdrant payload 到 DuckDB

3. 建立 Wiki 系統:
   - 目錄結構（papers/, concepts/, comparisons/, reviews/）
   - Frontmatter 解析器
   - Wiki 索引生成器
   - LintAgent（檢查 wiki 一致性）

4. 改寫 Ingest Pipeline:
   - DOI 提取（CrossRef API）
   - 自動重命名
   - Markdown 生成
   - 資料庫註冊
   - 向量化和 Qdrant 存儲
```

**Phase 2：進階功能（2-3 週）**
```yaml
- 可信度系統（完整版）
- Persona 系統
- 文獻回顧生成
```

**Phase 3：測試和文件（1 週）**

**總時間**：5-6 週

**風險**：
- 🔴 可能破壞現有功能
- 🔴 Marker 整合可能遇到技術問題
- 🔴 DuckDB 遷移可能遺失資料
- 🔴 過度設計（可能很多功能用不到）

---

#### **路徑 C：混合式（平衡）**

**目標**：保留現有架構，選擇性加入關鍵功能

**Phase 1：最小 DuckDB 整合（1.5 週）**
```yaml
1. 並行雙資料庫:
   - Qdrant: 繼續用於向量搜尋（不改）
   - DuckDB: 只存結構化元數據（新增）

2. 元數據層:
   - 建立 pdfs, journals, authors 表
   - DOI 提取（用 PyMuPDF 元數據，不查 API）
   - 期刊識別（靜態 Beall's List）

3. 不改動:
   - ❌ 不整合 Marker（繼續用 PyMuPDF）
   - ❌ 不建立 Wiki 系統
   - ✅ Qdrant 繼續存 chunks
```

**Phase 2：可信度系統（1 週）**
```yaml
- CredibilityAgent（基於 DuckDB 元數據）
- CLI 指令（assess, list-flagged）
```

**Phase 3：評估下一步（0.5 週）**
```yaml
決策:
  - DuckDB 效果如何？
  - 是否需要 Wiki？
  - 是否需要 Marker？
  - 是否繼續 Persona 和文獻回顧？
```

**總時間**：3 週（到決策點）

**優勢**：
- ✅ 風險可控（逐步驗證）
- ✅ 不破壞現有程式碼
- ✅ 保留靈活性（可隨時調整方向）

---

## 第六部分：關鍵決策問題

在選擇路徑前，需要回答以下問題：

### Q1: Marker 是否真的必要？

**設計假設**：
- Marker 生成高品質 markdown（給 Wiki 系統用）
- 保留 LaTeX 公式、複雜表格

**現實考量**：
- PyMuPDF 的 markdown 轉換（`page.get_text("markdown")`）可能就夠用
- Marker 需要額外安裝（Docker/CUDA）
- 學術 PDF 的複雜度（表格、公式）是否真的需要完美保留？

**驗證方式**：
```python
# 快速測試 PyMuPDF 的 markdown 品質
import fitz
doc = fitz.open("attention-is-all-you-need.pdf")
markdown = doc[0].get_text("markdown")
# 看看效果如何
```

**決策標準**：
- 如果 PyMuPDF markdown 品質 > 80% 可用 → **不需要 Marker**
- 如果 LaTeX 公式完全遺失 → **需要 Marker**

---

### Q2: Wiki 系統是否真的必要？

**設計假設**：
- Wiki 作為知識快取層（Karpathy 模式）
- 減少 RAG overhead
- 人類可讀

**現實考量**：
- DuckDB 可以存結構化元數據（不需要 markdown 檔案）
- Qdrant 可以存 chunks（已經有快取）
- Wiki 檔案系統增加維護成本（同步問題）

**替代方案**：
```yaml
方案 A（Wiki 檔案系統）:
  優點: 人類可讀、可版本控制、支援 git
  缺點: 需要同步機制、增加複雜度

方案 B（純資料庫）:
  優點: 單一資料來源、無同步問題
  缺點: 無法手動編輯、不可讀
  
方案 C（混合）:
  Wiki 只存「編撰的內容」（比較、綜述）
  原始論文只存資料庫
```

**決策標準**：
- 如果需要「人工編輯 wiki 條目」 → **需要 Wiki**
- 如果只是「自動生成知識」 → **資料庫就夠**

---

### Q3: DuckDB vs SQLite？

**設計假設**：
- DuckDB 分析查詢快（OLAP）
- 原生支援 JSON/struct types
- 可查詢 parquet

**現實考量**：
- 資料量很小（100-200 篇論文）
- SQLite 夠用且更成熟
- DuckDB 增加學習成本

**決策標準**：
```sql
-- 如果需要這種查詢
SELECT json_extract_path(metadata, 'authors[0].h_index') 
FROM pdfs;
-- 那麼 DuckDB 的 JSON 支援更好

-- 如果只需要簡單查詢
SELECT title, year FROM pdfs WHERE year > 2020;
-- 那麼 SQLite 就夠了
```

**建議**：
- Phase 1 用 SQLite（標準庫，無風險）
- 如果發現效能或功能不足，再遷移到 DuckDB

---

### Q4: 是否需要外部 API？

**設計假設**：
- CrossRef API（DOI 查詢）
- Semantic Scholar API（論文推薦、h-index）
- DOAJ API（期刊驗證）

**現實考量**：
- 增加外部依賴（網路、API key）
- 可能有 rate limit
- 離線不可用

**替代方案**：
```yaml
階段 1（無 API）:
  - 使用靜態資料（Beall's List JSON）
  - 從 PDF 元數據提取（不驗證）
  
階段 2（可選 API）:
  - 加入 CrossRef（如果需要精確 DOI）
  - 加入 Semantic Scholar（如果需要 h-index）
```

**決策標準**：
- 如果「識別掠奪期刊」就夠 → **不需要 API**（靜態名單）
- 如果需要「即時引用數、h-index」 → **需要 API**

---

## 建議的執行策略

### 🎯 **推薦：路徑 A（漸進式增量）**

#### **Week 1：最小可行可信度系統**

**目標**：在現有架構上加入基礎可信度評估，不做大規模重構

**具體任務**：

```yaml
Day 1-2: 資料層
  - 新增 src/capsa/storage/metadata_db.py（SQLite wrapper）
  - 定義 schema（journals, authors, pdfs 三個表）
  - 下載 Beall's List（轉成 JSON 或直接存 DB）
  
Day 3-4: Agent 實作
  - 新增 src/capsa/agents/credibility_agent.py
  - 實作基礎評分邏輯（期刊檢查 + 簡單評分）
  - 整合到現有的 Orchestrator
  
Day 5: CLI 整合
  - 新增 `capsa assess <pdf>` 指令
  - 新增 `capsa list-flagged` 指令
  - 美化輸出（rich table）
  
Day 6-7: 測試和文件
  - 寫單元測試（pytest）
  - 更新 README（新功能說明）
  - 寫使用範例
```

#### **Week 1 結束後的決策點**

```yaml
評估問題:
  1. SQLite 效能如何？
     → 如果慢：考慮 DuckDB
     → 如果夠快：繼續用 SQLite
  
  2. 靜態 Beall's List 是否夠用？
     → 如果夠：不需要 API
     → 如果不夠：加入 CrossRef API
  
  3. 使用者反饋如何？
     → 如果實用：繼續 Phase 2（Persona 系統）
     → 如果不實用：重新評估方向
```

#### **Week 2-3：根據決策點調整**

**情境 A：SQLite + 靜態資料夠用**
```yaml
→ 繼續實作 Persona 系統（不需要 Wiki）
→ Persona 定義存在 metadata_db 的 reader_personas 表
→ 點評記錄存在 persona_reviews 表
```

**情境 B：需要 DuckDB + API**
```yaml
→ 遷移 SQLite → DuckDB
→ 整合 CrossRef API
→ 然後再實作 Persona 系統
```

**情境 C：方向調整**
```yaml
→ 如果使用者更需要「智慧搜尋」而不是「可信度評估」
→ 轉向加強 QueryAgent（例如加入 reranking）
→ 或實作 CompareAgent 的進階功能
```

---

### 不推薦：路徑 B（完整重構）

**理由**：
- 🔴 6 週工時太長（機會成本高）
- 🔴 破壞現有可用程式碼（風險高）
- 🔴 可能過度設計（很多功能用不到）
- 🔴 無法快速驗證概念

**唯一適用場景**：
- 如果你確定要完全按照設計文件的願景實作
- 且願意接受 6 週的開發時間
- 且確定不會改變方向

---

## 附錄：快速驗證腳本

### 驗證 PyMuPDF markdown 品質

```python
"""測試 PyMuPDF 的 markdown 轉換是否夠用"""
import fitz

def test_markdown_quality(pdf_path: str):
    doc = fitz.open(pdf_path)
    
    # 測試第一頁
    page = doc[0]
    
    # PyMuPDF 的 markdown
    markdown = page.get_text("markdown")
    
    print("=== PyMuPDF Markdown ===")
    print(markdown[:500])
    
    # 對比原始文字
    text = page.get_text("text")
    print("\n=== Raw Text ===")
    print(text[:500])
    
    # 檢查是否有 LaTeX
    has_latex = "$" in text or "\\(" in text
    print(f"\n檢測到 LaTeX 公式: {has_latex}")
    
    if has_latex:
        print("⚠️ 如果需要保留 LaTeX，可能需要 Marker")
    else:
        print("✅ PyMuPDF markdown 應該夠用")

# 執行測試
test_markdown_quality("path/to/sample.pdf")
```

### 驗證 SQLite vs DuckDB 效能

```python
"""比較 SQLite 和 DuckDB 查詢效能"""
import sqlite3
import duckdb
import time

def benchmark_db():
    # 模擬 200 篇論文的查詢
    
    # SQLite
    conn_sqlite = sqlite3.connect(":memory:")
    # ... 建立表和插入資料
    
    start = time.time()
    # 執行複雜查詢
    conn_sqlite.execute("""
        SELECT p.title, AVG(a.h_index)
        FROM pdfs p
        JOIN pdf_author_link pal ON p.id = pal.pdf_id
        JOIN authors a ON pal.author_id = a.id
        GROUP BY p.title
    """)
    sqlite_time = time.time() - start
    
    # DuckDB
    conn_duck = duckdb.connect(":memory:")
    # ... 建立表和插入資料
    
    start = time.time()
    # 執行相同查詢
    conn_duck.execute("""
        SELECT p.title, AVG(a.h_index)
        FROM pdfs p
        JOIN pdf_author_link pal ON p.id = pal.pdf_id
        JOIN authors a ON pal.author_id = a.id
        GROUP BY p.title
    """)
    duck_time = time.time() - start
    
    print(f"SQLite: {sqlite_time:.4f}s")
    print(f"DuckDB: {duck_time:.4f}s")
    print(f"速度差異: {sqlite_time / duck_time:.2f}x")
    
    if duck_time < sqlite_time * 0.5:
        print("✅ DuckDB 明顯更快，值得用")
    else:
        print("⚠️ SQLite 夠快，不需要換")
```

---

## 總結

### 關鍵發現

1. **設計文件描述的是「理想系統」，現有程式碼是「MVP 原型」**
   - 差距：3-4 週基礎架構 + 3-4 週進階功能 = **6-8 週**
   
2. **現有程式碼的優勢**：
   - ✅ PyMuPDF + Qdrant 的核心可用
   - ✅ Agent 架構清晰（易擴展）
   - ✅ MCP 整合完成（可立即用於 Claude Desktop）
   
3. **最大的架構缺口**：
   - ❌ **無結構化資料庫**（只有 Qdrant，無法做複雜查詢）
   - ❌ **無元數據管理**（DOI、期刊、作者）
   - ❌ **無 Wiki 系統**（無法做知識複利）

### 建議的下一步

**推薦路徑 A（漸進式增量）**：

1. **Week 1**：實作最小可行可信度系統（SQLite + 靜態資料）
2. **Week 1 結束**：評估效果，決定是否需要 DuckDB/API/Wiki
3. **Week 2-3**：根據評估結果，選擇性加入進階功能

**為什麼推薦這個路徑**：
- ✅ 快速驗證（1 週看到成果）
- ✅ 低風險（不破壞現有程式碼）
- ✅ 靈活（可隨時調整方向）
- ✅ 實用（識別掠奪期刊立即有價值）

**不推薦的路徑**：
- ❌ 完整重構（6 週工時，高風險，可能過度設計）

---

**本文件狀態**：完整分析，協助技術決策
**下一步**：選擇路徑，開始實作
