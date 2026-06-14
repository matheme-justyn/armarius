# Capsa 進階功能設計文件

> 設計日期：2026-06-11
> 
> 本文件設計三大進階學術功能：(1) 可信度管理系統、(2) Reader Persona 系統、(3) 互動式文獻回顧生成

---

## 目錄

1. [功能概述](#功能概述)
2. [可信度管理系統](#可信度管理系統)
3. [Reader Persona 系統](#reader-persona-系統)
4. [互動式文獻回顧生成](#互動式文獻回顧生成)
5. [資料庫擴展](#資料庫擴展)
6. [Agent 擴展](#agent-擴展)
7. [實作路線圖](#實作路線圖)

---

## 功能概述

### 核心問題
傳統文獻管理工具缺少：
1. **品質判斷**：無法區分優質期刊和掠奪性期刊
2. **多視角解讀**：只有單一維度的摘要
3. **主動研究引導**：不能識別研究 gap 並引導補充

### Capsa 的解決方案

```
PDF Ingest
    ↓
可信度評估（自動 + 手動）
    ↓
多 Persona 點評（老師視角、工程師視角、自己視角）
    ↓
Wiki 知識累積
    ↓
文獻回顧生成（識別 gaps → 建議補充 → 迭代改進）
```

---

## 可信度管理系統

### 需求分析

#### **三層可信度追蹤**

```
1. 期刊層級（Journal Level）
   - 掠奪性期刊偵測
   - Impact Factor / h-index
   - 出版社信譽

2. 作者層級（Author Level）
   - 作者的 h-index
   - 機構背景
   - 歷史發表記錄

3. 單篇論文層級（Paper Level）
   - 引用次數
   - 同行評審品質
   - 方法學嚴謹度
   - 用戶手動點評
```

---

### 資料模型設計

#### **DuckDB Schema 擴展**

```sql
-- 期刊可信度表
CREATE TABLE journals (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    issn TEXT,
    publisher TEXT,
    
    -- 可信度指標
    impact_factor FLOAT,
    h_index INTEGER,
    is_predatory BOOLEAN DEFAULT false,     -- 掠奪性期刊標記
    predatory_reason TEXT,                  -- 標記原因
    credibility_score FLOAT,                -- 綜合可信度 0-100
    
    -- 元數據
    source TEXT,                            -- 資料來源（beall's list, scopus, etc）
    verified_at TIMESTAMP,
    notes TEXT
);

-- 作者可信度表
CREATE TABLE authors (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    orcid TEXT UNIQUE,
    
    -- 可信度指標
    h_index INTEGER,
    citation_count INTEGER,
    institution TEXT,
    country TEXT,
    
    -- 歷史統計
    total_papers INTEGER DEFAULT 0,
    predatory_papers INTEGER DEFAULT 0,     -- 在掠奪期刊發表數
    
    credibility_score FLOAT,
    notes TEXT
);

-- 論文可信度表（擴展現有 pdfs 表）
ALTER TABLE pdfs ADD COLUMN credibility_score FLOAT;
ALTER TABLE pdfs ADD COLUMN credibility_notes TEXT;
ALTER TABLE pdfs ADD COLUMN citation_count INTEGER;
ALTER TABLE pdfs ADD COLUMN peer_review_quality TEXT;   -- 'high' | 'medium' | 'low' | 'unknown'
ALTER TABLE pdfs ADD COLUMN methodology_rigor TEXT;     -- 'rigorous' | 'moderate' | 'weak'
ALTER TABLE pdfs ADD COLUMN user_rating FLOAT;          -- 1-5 星
ALTER TABLE pdfs ADD COLUMN flagged_issues JSON;        -- ['data_fabrication', 'conflict_of_interest']

-- 期刊-論文關聯
CREATE TABLE pdf_journal_link (
    pdf_id INTEGER REFERENCES pdfs(id),
    journal_id INTEGER REFERENCES journals(id),
    PRIMARY KEY (pdf_id, journal_id)
);

-- 作者-論文關聯
CREATE TABLE pdf_author_link (
    pdf_id INTEGER REFERENCES pdfs(id),
    author_id INTEGER REFERENCES authors(id),
    author_order INTEGER,                   -- 第幾作者
    PRIMARY KEY (pdf_id, author_id)
);
```

---

### 自動可信度評估

#### **CredibilityAgent**

```python
# src/capsa/agents/credibility_agent.py

from dataclasses import dataclass
from typing import List, Dict
import requests

@dataclass
class CredibilityAssessment:
    """可信度評估結果"""
    journal_score: float        # 0-100
    author_score: float         # 0-100
    paper_score: float          # 0-100
    overall_score: float        # 加權平均
    
    flags: List[str]            # ['predatory_journal', 'low_citation']
    warnings: List[str]         # 警告訊息
    recommendations: List[str]   # 建議


class CredibilityAgent:
    """評估論文可信度"""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.bealls_list = self._load_predatory_journals()
    
    def assess_paper(self, pdf_id: int) -> CredibilityAssessment:
        """
        評估單篇論文可信度
        
        流程：
        1. 檢查期刊（是否在掠奪名單）
        2. 檢查作者（h-index, 機構）
        3. 檢查論文本身（引用數、方法學）
        4. 綜合評分
        """
        paper = self.db.execute("SELECT * FROM pdfs WHERE id = ?", (pdf_id,)).fetchone()
        
        # 1. 期刊評估
        journal_score = self._assess_journal(paper['journal'])
        
        # 2. 作者評估
        authors = self._get_authors(pdf_id)
        author_score = self._assess_authors(authors)
        
        # 3. 論文本身評估
        paper_score = self._assess_paper_content(pdf_id)
        
        # 4. 綜合評分（加權）
        overall_score = (
            journal_score * 0.4 +    # 期刊權重 40%
            author_score * 0.3 +     # 作者權重 30%
            paper_score * 0.3        # 論文本身 30%
        )
        
        # 5. 產生警告和建議
        flags, warnings, recommendations = self._generate_insights(
            journal_score, author_score, paper_score
        )
        
        return CredibilityAssessment(
            journal_score=journal_score,
            author_score=author_score,
            paper_score=paper_score,
            overall_score=overall_score,
            flags=flags,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _assess_journal(self, journal_name: str) -> float:
        """
        評估期刊可信度
        
        資料來源：
        1. Beall's List（掠奪性期刊名單）
        2. Scopus / Web of Science（Impact Factor）
        3. DOAJ（Directory of Open Access Journals）
        """
        # 檢查是否在掠奪名單
        if journal_name in self.bealls_list:
            return 0.0  # 掠奪期刊直接 0 分
        
        # 查詢 Impact Factor（可以用 CrossRef API 或本地資料庫）
        impact_factor = self._get_impact_factor(journal_name)
        
        if impact_factor is None:
            return 50.0  # 查不到，給中等分數
        
        # 根據 IF 計算分數（簡化版本）
        if impact_factor > 10:
            return 90.0
        elif impact_factor > 5:
            return 80.0
        elif impact_factor > 2:
            return 70.0
        else:
            return 60.0
    
    def _assess_authors(self, authors: List[Dict]) -> float:
        """
        評估作者群可信度
        
        重點關注第一作者和通訊作者
        """
        if not authors:
            return 50.0  # 沒有作者資訊，給中等分
        
        scores = []
        
        for author in authors:
            # 查詢作者的 h-index（可以用 Google Scholar API 或 ORCID）
            h_index = self._get_author_hindex(author['name'], author.get('orcid'))
            
            if h_index is None:
                score = 50.0
            elif h_index > 50:
                score = 95.0
            elif h_index > 20:
                score = 85.0
            elif h_index > 10:
                score = 75.0
            else:
                score = 60.0
            
            # 第一作者和通訊作者權重更高
            if author['author_order'] == 1:
                scores.append(score * 1.5)  # 第一作者權重 1.5x
            else:
                scores.append(score)
        
        return min(sum(scores) / len(scores), 100.0)
    
    def _assess_paper_content(self, pdf_id: int) -> float:
        """
        評估論文本身的品質
        
        指標：
        1. 引用次數（from Google Scholar API）
        2. 發表時間（太舊的打折）
        3. 方法學嚴謹度（用 LLM 評估）
        """
        paper = self.db.execute("SELECT * FROM pdfs WHERE id = ?", (pdf_id,)).fetchone()
        
        score = 50.0  # 基礎分
        
        # 引用次數
        if paper['citation_count']:
            if paper['citation_count'] > 100:
                score += 20
            elif paper['citation_count'] > 50:
                score += 15
            elif paper['citation_count'] > 10:
                score += 10
        
        # 發表時間（越新越好，但經典論文除外）
        if paper['year']:
            age = 2026 - paper['year']
            if age <= 2:
                score += 10  # 最新論文
            elif age <= 5:
                score += 5
            elif age > 20 and paper['citation_count'] > 100:
                score += 15  # 經典論文
        
        return min(score, 100.0)
    
    def _generate_insights(self, journal_score, author_score, paper_score):
        """生成警告和建議"""
        flags = []
        warnings = []
        recommendations = []
        
        # 掠奪期刊警告
        if journal_score == 0:
            flags.append('predatory_journal')
            warnings.append('⚠️ 此論文發表於掠奪性期刊，請謹慎引用')
            recommendations.append('尋找發表在正規期刊的相似研究')
        
        # 低引用警告
        if paper_score < 40:
            flags.append('low_citation')
            warnings.append('⚠️ 此論文引用數較低，可能影響力有限')
            recommendations.append('查找該領域的綜述文章以獲得更全面的理解')
        
        # 作者可信度低
        if author_score < 50:
            flags.append('unknown_authors')
            warnings.append('⚠️ 作者學術背景資訊不足')
            recommendations.append('檢查作者的其他發表記錄')
        
        return flags, warnings, recommendations
    
    def _load_predatory_journals(self) -> set:
        """
        載入掠奪性期刊名單
        
        資料來源：
        - Beall's List
        - DOAJ revoked journals
        - Cabell's Predatory Reports（需付費）
        """
        # 簡化版本：從本地檔案載入
        # 實際應該定期更新
        predatory_file = Path("~/.capsa/data/predatory_journals.txt").expanduser()
        if predatory_file.exists():
            return set(predatory_file.read_text().splitlines())
        return set()
    
    def _get_impact_factor(self, journal_name: str) -> float | None:
        """
        獲取期刊 Impact Factor
        
        可以整合：
        - Scopus API
        - Web of Science API
        - 本地資料庫（定期更新）
        """
        # TODO: 實作 API 查詢
        return None
    
    def _get_author_hindex(self, author_name: str, orcid: str = None) -> int | None:
        """
        獲取作者 h-index
        
        可以整合：
        - ORCID API
        - Google Scholar（非官方）
        - Semantic Scholar API
        """
        # TODO: 實作 API 查詢
        return None
```

---

### 使用者介面

#### **CLI 指令**

```bash
# 評估單篇論文
capsa assess paper.pdf
# 輸出：
# ✅ Overall Credibility: 78/100
# 📊 Journal: Nature (95/100)
# 👤 Authors: High h-index (85/100)
# 📄 Paper: 150 citations (70/100)

# 批次評估
capsa assess ~/Documents/papers/ --output report.json

# 標記掠奪期刊
capsa flag-journal "Journal of XXX" --reason "In Beall's list"

# 查看可信度分布
capsa credibility-stats
# 輸出：
# High (80-100): 15 papers
# Medium (60-79): 23 papers
# Low (0-59): 3 papers ⚠️
```

#### **Web UI**

```
論文詳情頁：
┌─────────────────────────────────────┐
│ Attention Is All You Need           │
│ Vaswani et al., 2017                │
├─────────────────────────────────────┤
│ 可信度評分：⭐⭐⭐⭐⭐ (95/100)         │
│                                     │
│ 📊 期刊：NeurIPS                    │
│    Impact Factor: 9.2 ✅            │
│                                     │
│ 👤 作者：                           │
│    Ashish Vaswani (h-index: 45) ✅  │
│    Google Research ✅                │
│                                     │
│ 📄 論文品質：                        │
│    引用數：15,234 ✅                 │
│    發表年份：2017 (經典論文)         │
│                                     │
│ 💬 用戶評價：⭐⭐⭐⭐⭐ (你的評分)      │
│    [編輯評價]                        │
└─────────────────────────────────────┘
```

---

## Reader Persona 系統

### 概念

**Persona = 一種閱讀視角的「蒸餾」**

不同讀者關心的面向不同：
- **老師視角**：教學價值、概念清晰度、適合教學的例子
- **工程師視角**：可實作性、程式碼品質、效能考量
- **研究者視角**：方法學創新、實驗設計、未來研究方向

### 資料模型

```sql
-- Reader Persona 定義表
CREATE TABLE reader_personas (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,              -- 'my_teacher' | 'engineer' | 'myself'
    display_name TEXT,                      -- '我的老師' | '工程師視角'
    description TEXT,                       -- 這個 persona 的特徵描述
    
    -- Persona 的關注面向（JSON）
    focus_areas JSON,                       -- ['teaching_value', 'code_quality', 'innovation']
    
    -- Prompt 模板
    system_prompt TEXT,                     -- LLM system prompt
    review_template TEXT,                   -- 點評模板
    
    -- 元數據
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- 論文點評表（多 persona）
CREATE TABLE paper_reviews (
    id INTEGER PRIMARY KEY,
    pdf_id INTEGER REFERENCES pdfs(id),
    persona_id INTEGER REFERENCES reader_personas(id),
    
    -- 點評內容
    review_text TEXT NOT NULL,
    key_insights JSON,                      -- ['insight1', 'insight2']
    strengths JSON,                         -- ['strength1', 'strength2']
    weaknesses JSON,                        -- ['weakness1', 'weakness2']
    recommendations TEXT,                   -- 建議
    
    -- 評分（可選）
    rating FLOAT,                           -- 1-5 星
    relevance_score FLOAT,                  -- 對這個 persona 的相關性
    
    -- 元數據
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(pdf_id, persona_id)              -- 每篇論文每個 persona 只有一個點評
);
```

---

### Persona 定義範例

#### **1. 老師視角**

```yaml
# personas/teacher.yaml

name: my_teacher
display_name: 我的老師（教學視角）
description: |
  一位資深教授，關注論文的教學價值和概念清晰度。
  重視理論基礎、是否適合課堂教學、能否啟發學生。

focus_areas:
  - teaching_value        # 教學價值
  - concept_clarity       # 概念清晰度
  - foundational_theory   # 理論基礎
  - pedagogical_examples  # 教學範例

system_prompt: |
  你是一位資深教授，正在評估這篇論文是否適合用於教學。
  
  請從以下面向評論：
  1. **教學價值**：這篇論文是否適合作為課堂教材？
  2. **概念清晰度**：核心概念是否解釋得清楚？
  3. **理論基礎**：理論背景是否扎實？
  4. **教學範例**：是否有好的例子可以用於課堂？
  
  請提供：
  - 3-5 個關鍵洞見
  - 優點和缺點
  - 教學建議（如何在課堂上使用）

review_template: |
  ## 教學評估
  
  ### 教學價值
  {teaching_value}
  
  ### 概念清晰度
  {concept_clarity}
  
  ### 適合課程
  {suitable_courses}
  
  ### 教學建議
  {teaching_recommendations}
```

#### **2. 工程師視角**

```yaml
# personas/engineer.yaml

name: engineer
display_name: 工程師視角
description: |
  一位實務導向的工程師，關注論文的可實作性、程式碼品質、效能考量。

focus_areas:
  - implementability      # 可實作性
  - code_quality          # 程式碼品質
  - performance           # 效能
  - scalability           # 可擴展性
  - production_readiness  # 生產就緒度

system_prompt: |
  你是一位經驗豐富的工程師，正在評估這篇論文的實作價值。
  
  請從以下面向評論：
  1. **可實作性**：這個方法容易實作嗎？
  2. **程式碼品質**：如果有程式碼，品質如何？
  3. **效能考量**：時間/空間複雜度如何？
  4. **可擴展性**：能否應用到大規模場景？
  5. **生產就緒度**：能否直接用於生產環境？
  
  請提供：
  - 實作難點
  - 效能瓶頸
  - 工程建議

review_template: |
  ## 工程評估
  
  ### 實作難度
  {implementation_difficulty}
  
  ### 效能分析
  {performance_analysis}
  
  ### 工程建議
  {engineering_recommendations}
```

#### **3. 研究者視角（自己）**

```yaml
# personas/myself.yaml

name: myself
display_name: 我自己（研究視角）
description: |
  我自己的研究視角，關注方法學創新、實驗設計、未來研究方向。

focus_areas:
  - methodological_innovation  # 方法學創新
  - experimental_design        # 實驗設計
  - future_research            # 未來研究方向
  - related_work              # 相關工作
  - research_gaps             # 研究 gap

system_prompt: |
  你是一位研究者，正在深度分析這篇論文的學術價值。
  
  請從以下面向評論：
  1. **方法學創新**：提出了什麼新方法？
  2. **實驗設計**：實驗設計是否嚴謹？
  3. **研究 Gap**：發現了哪些未解決的問題？
  4. **未來方向**：可以延伸哪些研究？
  
  請提供：
  - 核心貢獻
  - 方法學優缺點
  - 可延伸的研究方向

review_template: |
  ## 研究評估
  
  ### 核心貢獻
  {core_contributions}
  
  ### 方法學分析
  {methodological_analysis}
  
  ### 研究 Gap
  {research_gaps}
  
  ### 未來方向
  {future_directions}
```

---

### ReviewAgent（點評生成）

```python
# src/capsa/agents/review_agent.py

from typing import List, Dict
import yaml

class ReviewAgent:
    """為論文生成多視角點評"""
    
    def __init__(self, db_conn, llm_client):
        self.db = db_conn
        self.llm = llm_client
        self.personas = self._load_personas()
    
    def review_paper(
        self, 
        pdf_id: int, 
        persona_name: str,
        force_regenerate: bool = False
    ) -> Dict:
        """
        用指定 persona 點評論文
        
        Args:
            pdf_id: 論文 ID
            persona_name: Persona 名稱（'my_teacher' | 'engineer' | 'myself'）
            force_regenerate: 是否強制重新生成（否則讀取快取）
        """
        # 1. 檢查是否已有點評
        if not force_regenerate:
            existing_review = self._get_existing_review(pdf_id, persona_name)
            if existing_review:
                return existing_review
        
        # 2. 載入 persona
        persona = self.personas[persona_name]
        
        # 3. 獲取論文內容
        paper_content = self._get_paper_content(pdf_id)
        
        # 4. 生成點評
        review = self._generate_review(paper_content, persona)
        
        # 5. 儲存到資料庫
        self._save_review(pdf_id, persona['id'], review)
        
        return review
    
    def batch_review(
        self, 
        pdf_ids: List[int], 
        persona_names: List[str]
    ) -> Dict[int, Dict[str, Dict]]:
        """
        批次點評
        
        Returns:
            {
                pdf_id: {
                    'my_teacher': review_dict,
                    'engineer': review_dict,
                    ...
                }
            }
        """
        results = {}
        
        for pdf_id in pdf_ids:
            results[pdf_id] = {}
            for persona_name in persona_names:
                review = self.review_paper(pdf_id, persona_name)
                results[pdf_id][persona_name] = review
        
        return results
    
    def _load_personas(self) -> Dict:
        """從資料庫或 YAML 載入 personas"""
        personas = {}
        
        # 從 personas/ 目錄載入 YAML 定義
        persona_dir = Path("~/.capsa/personas").expanduser()
        if persona_dir.exists():
            for yaml_file in persona_dir.glob("*.yaml"):
                with open(yaml_file) as f:
                    persona_data = yaml.safe_load(f)
                    personas[persona_data['name']] = persona_data
        
        return personas
    
    def _generate_review(self, paper_content: str, persona: Dict) -> Dict:
        """用 LLM 生成點評"""
        prompt = f"""
{persona['system_prompt']}

論文內容：
{paper_content}

請按照以下格式提供點評：

1. 關鍵洞見（3-5 點）
2. 優點（2-3 點）
3. 缺點（2-3 點）
4. 建議
5. 評分（1-5 星）
"""
        
        response = self.llm.complete(prompt)
        
        # 解析 LLM 回應
        review = {
            'review_text': response,
            'key_insights': self._extract_insights(response),
            'strengths': self._extract_strengths(response),
            'weaknesses': self._extract_weaknesses(response),
            'recommendations': self._extract_recommendations(response),
            'rating': self._extract_rating(response)
        }
        
        return review
```

---

### 使用範例

#### **CLI**

```bash
# 用「老師視角」點評單篇論文
capsa review paper.pdf --persona my_teacher

# 批次點評（所有 persona）
capsa review ~/Documents/papers/ --personas all

# 查看特定論文的所有點評
capsa review-list paper.pdf

# 比較不同 persona 的點評
capsa review-compare paper.pdf
```

#### **輸出範例**

```markdown
# Attention Is All You Need - 多視角點評

## 👨‍🏫 老師視角

### 教學價值 ⭐⭐⭐⭐⭐
這篇論文非常適合作為深度學習課程的教材。Transformer 架構是現代 NLP 的基礎，
概念清晰、圖表豐富。

### 關鍵洞見
1. Self-attention 機制比 RNN 更容易並行化
2. Positional encoding 解決了序列位置問題
3. Multi-head attention 提供了多視角的表徵學習

### 教學建議
- 適合「深度學習」、「自然語言處理」課程
- 建議搭配實作作業（實作簡化版 Transformer）
- 重點講解 attention 的計算過程

---

## 👨‍💻 工程師視角

### 實作難度 ⭐⭐⭐☆☆
中等難度。PyTorch 有現成的 `nn.Transformer`，但從頭實作需要理解細節。

### 關鍵洞見
1. 比 RNN 容易並行化，訓練速度快
2. 但推理時記憶體消耗大（O(n²) attention）
3. 適合 GPU 加速

### 工程建議
- 生產環境建議用 HuggingFace Transformers
- 注意序列長度限制（記憶體問題）
- 可以用 Flash Attention 優化

---

## 🔬 我自己（研究視角）

### 核心貢獻 ⭐⭐⭐⭐⭐
完全拋棄 RNN/CNN，純用 attention 達到 SOTA。

### 研究 Gap
1. 長序列處理仍有瓶頸（O(n²) 複雜度）
2. 可解釋性不足（attention weights 不一定代表因果）
3. 小數據場景效果待驗證

### 未來方向
- Efficient Transformers（Linformer, Performer）
- Vision Transformers（ViT）
- 探索 attention 的理論基礎
```

---

## 互動式文獻回顧生成

### 概念

**文獻回顧 = 一個迭代的研究過程**

```
1. 定義研究問題
   ↓
2. 生成初稿（基於現有 wiki）
   ↓
3. 識別 Gap（缺少哪些文獻）
   ↓
4. 建議補充（推薦相關論文）
   ↓
5. 用戶補充文獻
   ↓
6. 更新草稿
   ↓
7. 回饋改進
   ↓
8. 迭代直到滿意
```

---

### 資料模型

```sql
-- 文獻回顧項目表
CREATE TABLE literature_reviews (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    research_question TEXT,                 -- 研究問題
    scope TEXT,                             -- 範圍（時間、領域）
    
    -- 狀態
    status TEXT DEFAULT 'draft',            -- 'draft' | 'in_progress' | 'completed'
    current_version INTEGER DEFAULT 1,
    
    -- 元數據
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文獻回顧版本表（支援迭代）
CREATE TABLE review_versions (
    id INTEGER PRIMARY KEY,
    review_id INTEGER REFERENCES literature_reviews(id),
    version INTEGER NOT NULL,
    
    -- 內容
    content TEXT NOT NULL,                  -- Markdown 格式
    outline JSON,                           -- 大綱結構
    
    -- 包含的論文
    included_papers JSON,                   -- [pdf_id1, pdf_id2, ...]
    
    -- Gap 分析
    identified_gaps JSON,                   -- [{gap: "...", priority: "high"}]
    recommended_papers JSON,                -- [{title: "...", reason: "..."}]
    
    -- 元數據
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT                              -- 版本說明
);

-- 用戶回饋表
CREATE TABLE review_feedback (
    id INTEGER PRIMARY KEY,
    version_id INTEGER REFERENCES review_versions(id),
    
    feedback_type TEXT,                     -- 'gap' | 'improvement' | 'question'
    content TEXT NOT NULL,
    
    -- 狀態
    status TEXT DEFAULT 'pending',          -- 'pending' | 'addressed' | 'dismissed'
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### LiteratureReviewAgent

```python
# src/capsa/agents/literature_review_agent.py

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ResearchGap:
    """識別出的研究 gap"""
    description: str
    priority: str              # 'high' | 'medium' | 'low'
    related_topics: List[str]
    suggested_search_terms: List[str]


@dataclass
class PaperRecommendation:
    """推薦補充的論文"""
    title: str
    authors: str
    year: int
    reason: str               # 為什麼推薦
    relevance_score: float    # 0-1
    search_strategy: str      # 如何找到的


class LiteratureReviewAgent:
    """生成和管理互動式文獻回顧"""
    
    def __init__(self, db_conn, llm_client, wiki_manager):
        self.db = db_conn
        self.llm = llm_client
        self.wiki = wiki_manager
    
    def create_review(
        self, 
        title: str, 
        research_question: str,
        scope: Dict
    ) -> int:
        """
        創建新的文獻回顧項目
        
        Args:
            title: 回顧標題
            research_question: 研究問題
            scope: 範圍 {'years': [2020, 2024], 'topics': ['transformer', 'attention']}
        
        Returns:
            review_id
        """
        # 1. 創建項目
        cursor = self.db.execute("""
            INSERT INTO literature_reviews (title, research_question, scope)
            VALUES (?, ?, ?)
        """, (title, research_question, json.dumps(scope)))
        
        review_id = cursor.lastrowid
        
        # 2. 生成初稿
        self.generate_draft(review_id)
        
        return review_id
    
    def generate_draft(self, review_id: int) -> Dict:
        """
        生成文獻回顧初稿
        
        流程：
        1. 從 wiki 查詢相關內容
        2. 生成大綱
        3. 填充每個章節
        4. 識別 gaps
        5. 推薦補充論文
        """
        review = self._get_review(review_id)
        
        # 1. 查詢相關 wiki 頁面
        relevant_pages = self.wiki.search(review['research_question'])
        
        # 2. 生成大綱
        outline = self._generate_outline(review, relevant_pages)
        
        # 3. 填充內容
        content = self._generate_content(outline, relevant_pages)
        
        # 4. 識別 gaps
        gaps = self._identify_gaps(review, outline, relevant_pages)
        
        # 5. 推薦論文
        recommendations = self._recommend_papers(gaps)
        
        # 6. 儲存版本
        version_id = self._save_version(
            review_id=review_id,
            version=1,
            content=content,
            outline=outline,
            gaps=gaps,
            recommendations=recommendations
        )
        
        return {
            'version_id': version_id,
            'content': content,
            'outline': outline,
            'gaps': gaps,
            'recommendations': recommendations
        }
    
    def _generate_outline(self, review: Dict, relevant_pages: List) -> Dict:
        """
        生成文獻回顧大綱
        
        標準結構：
        1. Introduction
        2. Background
        3. Methodology (how we did the review)
        4. Main Body (分主題)
        5. Discussion
        6. Conclusion
        7. Future Work
        """
        prompt = f"""
你正在撰寫一篇文獻回顧："{review['title']}"

研究問題：{review['research_question']}

目前已有的相關 wiki 頁面：
{self._format_pages(relevant_pages)}

請生成一個文獻回顧的大綱（Outline）。

要求：
1. 遵循學術文獻回顧的標準結構
2. 根據現有內容設計章節
3. 識別可能缺少的部分

輸出 JSON 格式：
{{
  "sections": [
    {{
      "title": "Introduction",
      "subsections": ["Research Question", "Scope", "Structure"],
      "estimated_length": "2 pages",
      "key_points": ["...", "..."]
    }},
    ...
  ]
}}
"""
        response = self.llm.complete(prompt)
        outline = json.loads(response)
        
        return outline
    
    def _generate_content(self, outline: Dict, relevant_pages: List) -> str:
        """
        根據大綱生成內容
        
        逐章節生成，引用 wiki 頁面
        """
        content_parts = []
        
        for section in outline['sections']:
            section_content = self._generate_section(
                section, 
                relevant_pages
            )
            content_parts.append(section_content)
        
        # 組合成完整文檔
        content = "\n\n".join(content_parts)
        
        return content
    
    def _identify_gaps(
        self, 
        review: Dict, 
        outline: Dict, 
        relevant_pages: List
    ) -> List[ResearchGap]:
        """
        識別研究 gap
        
        策略：
        1. 分析大綱中哪些章節內容不足
        2. 檢查哪些關鍵主題沒有涵蓋
        3. 比對同領域經典論文（如果有）
        """
        prompt = f"""
你正在審閱一篇文獻回顧的初稿。

研究問題：{review['research_question']}
大綱：{json.dumps(outline, indent=2)}
已包含的內容來源數量：{len(relevant_pages)}

請識別以下類型的 Gap：
1. **內容 Gap**：哪些重要主題沒有涵蓋？
2. **方法 Gap**：是否缺少某些重要方法的討論？
3. **時間 Gap**：是否缺少最新或經典的研究？
4. **視角 Gap**：是否只涵蓋單一視角？

對每個 Gap，請提供：
- 描述
- 優先級（high/medium/low）
- 相關主題
- 建議的搜尋關鍵詞

輸出 JSON 格式。
"""
        
        response = self.llm.complete(prompt)
        gaps_data = json.loads(response)
        
        gaps = [
            ResearchGap(
                description=g['description'],
                priority=g['priority'],
                related_topics=g['related_topics'],
                suggested_search_terms=g['search_terms']
            )
            for g in gaps_data
        ]
        
        return gaps
    
    def _recommend_papers(self, gaps: List[ResearchGap]) -> List[PaperRecommendation]:
        """
        基於 gaps 推薦論文
        
        策略：
        1. 用 gap 的關鍵詞搜尋外部資料庫（Google Scholar, Semantic Scholar）
        2. 檢查現有 wiki 是否已提到但未索引
        3. 詢問 LLM 是否知道經典論文
        """
        recommendations = []
        
        for gap in gaps:
            # 搜尋外部資料庫
            search_results = self._search_external_papers(
                gap.suggested_search_terms
            )
            
            # 過濾和排序
            for paper in search_results:
                rec = PaperRecommendation(
                    title=paper['title'],
                    authors=paper['authors'],
                    year=paper['year'],
                    reason=f"Addresses gap: {gap.description}",
                    relevance_score=paper['relevance'],
                    search_strategy=f"Searched for: {gap.suggested_search_terms}"
                )
                recommendations.append(rec)
        
        # 按相關性排序
        recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return recommendations[:20]  # 最多推薦 20 篇
    
    def add_feedback(self, version_id: int, feedback: str, feedback_type: str):
        """
        用戶新增回饋
        
        類型：
        - 'gap': 發現新的 gap
        - 'improvement': 改進建議
        - 'question': 問題
        """
        self.db.execute("""
            INSERT INTO review_feedback (version_id, feedback_type, content)
            VALUES (?, ?, ?)
        """, (version_id, feedback_type, feedback))
    
    def iterate_version(self, review_id: int) -> Dict:
        """
        基於回饋迭代新版本
        
        流程：
        1. 收集所有 pending 的回饋
        2. 更新大綱
        3. 重新生成內容
        4. 識別新的 gaps
        """
        # 獲取最新版本
        latest_version = self._get_latest_version(review_id)
        
        # 獲取回饋
        feedbacks = self._get_pending_feedbacks(latest_version['id'])
        
        # 基於回饋更新
        updated_content = self._update_content_with_feedback(
            latest_version['content'],
            feedbacks
        )
        
        # 儲存新版本
        new_version = latest_version['version'] + 1
        version_id = self._save_version(
            review_id=review_id,
            version=new_version,
            content=updated_content,
            notes=f"Addressed {len(feedbacks)} feedbacks"
        )
        
        # 標記回饋為已處理
        for feedback in feedbacks:
            self.db.execute("""
                UPDATE review_feedback 
                SET status = 'addressed'
                WHERE id = ?
            """, (feedback['id'],))
        
        return self._get_version(version_id)
    
    def export_review(self, review_id: int, format: str = 'markdown') -> str:
        """
        匯出文獻回顧
        
        格式：
        - 'markdown': Markdown 檔案
        - 'latex': LaTeX 格式
        - 'docx': Word 文件
        - 'pdf': PDF（via pandoc）
        """
        latest_version = self._get_latest_version(review_id)
        content = latest_version['content']
        
        if format == 'markdown':
            return content
        elif format == 'latex':
            return self._convert_to_latex(content)
        elif format == 'docx':
            return self._convert_to_docx(content)
        elif format == 'pdf':
            return self._convert_to_pdf(content)
```

---

### 互動流程範例

```bash
# 1. 創建新的文獻回顧
capsa review-create \
  --title "Transformer Architecture: A Survey" \
  --question "How has the Transformer architecture evolved since 2017?" \
  --years 2017-2024 \
  --topics transformer,attention,nlp

# 輸出：
# ✅ Created review #1
# 📄 Generated initial draft (v1)
# 
# 📊 Current Status:
# - Included papers: 15
# - Identified gaps: 5
# - Recommended papers: 12
#
# ⚠️ High-priority gaps:
# 1. Missing coverage of Efficient Transformers (Linformer, Performer)
# 2. Limited discussion of Vision Transformers
# 3. No analysis of training efficiency techniques

# 2. 查看草稿
capsa review-show 1

# 3. 查看識別出的 gaps
capsa review-gaps 1
# 輸出：
# Gap #1 [HIGH]: Efficient Transformers
# - Missing: Linformer, Performer, Reformer
# - Suggested search: "efficient transformers", "linear attention"
# - Recommended papers:
#   1. "Linformer: Self-Attention with Linear Complexity" (Wang et al., 2020)
#   2. "Rethinking Attention with Performers" (Choromanski et al., 2020)

# 4. 補充論文
capsa index linformer.pdf
capsa index performer.pdf

# 5. 重新生成（自動包含新論文）
capsa review-regenerate 1
# 輸出：
# ✅ Generated version 2
# 📄 Added 2 new papers
# 🔄 Updated sections: "Efficient Attention Mechanisms"
# 📊 Remaining gaps: 3

# 6. 新增回饋
capsa review-feedback 1 \
  --type improvement \
  --content "應該更深入討論 Flash Attention"

# 7. 迭代
capsa review-iterate 1

# 8. 匯出
capsa review-export 1 --format pdf --output survey.pdf
```

---

### Web UI 互動介面

```
文獻回顧編輯器：
┌─────────────────────────────────────────────────┐
│ Transformer Architecture: A Survey              │
│ Version 2 (Draft) - Last updated: 2026-06-11    │
├─────────────────────────────────────────────────┤
│ [Outline] [Content] [Gaps] [Recommendations]   │
├─────────────────────────────────────────────────┤
│                                                 │
│ ## 1. Introduction                              │
│ The Transformer architecture, introduced by     │
│ Vaswani et al. (2017), revolutionized...       │
│                                                 │
│ [Show 15 citations]                             │
│                                                 │
│ ---                                             │
│                                                 │
│ ## 2. Core Mechanisms                           │
│ ### 2.1 Self-Attention                          │
│ ...                                             │
│                                                 │
│ ⚠️ Gap identified: Limited coverage of          │
│    efficient attention variants                 │
│    [View recommendations]                       │
│                                                 │
├─────────────────────────────────────────────────┤
│ 💬 Feedback                                     │
│ [Add feedback...]                               │
│                                                 │
│ Recent feedback:                                │
│ • "需要補充 Vision Transformer 的討論" (pending)│
│ • "Flash Attention 值得深入分析" (pending)      │
│                                                 │
├─────────────────────────────────────────────────┤
│ [Regenerate] [Export PDF] [Add Papers]         │
└─────────────────────────────────────────────────┘

Gaps 標籤：
┌─────────────────────────────────────────────────┐
│ Identified Gaps (3 remaining)                   │
├─────────────────────────────────────────────────┤
│ 🔴 HIGH: Efficient Transformers                 │
│    Missing: Linformer, Performer, Reformer      │
│    [Search Scholar] [Add Papers]                │
│                                                 │
│ 🟡 MEDIUM: Vision Transformers                  │
│    Needs deeper analysis of ViT variants        │
│    Recommended:                                 │
│    • "An Image is Worth 16x16 Words" (2020)     │
│    • "Swin Transformer" (2021)                  │
│    [Add to review]                              │
│                                                 │
│ 🟢 LOW: Training Efficiency                     │
│    Flash Attention, Gradient Checkpointing      │
└─────────────────────────────────────────────────┘
```

---

## 資料庫擴展總結

### DuckDB Schema（完整版）

```sql
-- ===== 可信度系統 =====

CREATE TABLE journals (...);
CREATE TABLE authors (...);
ALTER TABLE pdfs ADD COLUMN credibility_score FLOAT;
CREATE TABLE pdf_journal_link (...);
CREATE TABLE pdf_author_link (...);

-- ===== Persona 系統 =====

CREATE TABLE reader_personas (...);
CREATE TABLE paper_reviews (...);

-- ===== 文獻回顧系統 =====

CREATE TABLE literature_reviews (...);
CREATE TABLE review_versions (...);
CREATE TABLE review_feedback (...);
```

---

## Agent 擴展總結

### 新增 Agents

```python
# src/capsa/agents/

credibility_agent.py      # 可信度評估
review_agent.py           # Persona 點評生成
literature_review_agent.py # 文獻回顧生成
gap_analysis_agent.py     # Gap 識別（可以整合進 literature_review_agent）
```

---

## 實作路線圖

### Phase 1：可信度系統（2 週）

**Week 1**：
- Day 1-3：DuckDB schema 擴展（journals, authors 表）
- Day 4-5：CredibilityAgent 基礎實作
- Day 6-7：整合 Beall's List、CrossRef API

**Week 2**：
- Day 8-10：CLI 指令（`capsa assess`）
- Day 11-12：Web UI 顯示可信度
- Day 13-14：測試和文件

---

### Phase 2：Persona 系統（2 週）

**Week 3**：
- Day 15-17：Persona 定義系統（YAML 載入）
- Day 18-19：ReviewAgent 實作
- Day 20-21：批次點評功能

**Week 4**：
- Day 22-24：CLI 指令（`capsa review`）
- Day 25-26：Web UI 多視角展示
- Day 27-28：測試和文件

---

### Phase 3：文獻回顧系統（3 週）

**Week 5**：
- Day 29-31：LiteratureReviewAgent 基礎實作
- Day 32-33：大綱生成邏輯
- Day 34-35：內容生成邏輯

**Week 6**：
- Day 36-38：Gap 識別邏輯
- Day 39-40：論文推薦邏輯（整合 Semantic Scholar API）
- Day 41-42：迭代更新邏輯

**Week 7**：
- Day 43-45：CLI 指令（`capsa review-create`, `capsa review-iterate`）
- Day 46-48：Web UI 互動介面
- Day 49：匯出功能（Markdown, LaTeX, PDF）

---

## 技術債務與風險

### 外部 API 依賴

| API | 用途 | 風險 | 緩解策略 |
|-----|------|------|----------|
| CrossRef | DOI 元數據 | Rate limit | 本地快取 |
| Semantic Scholar | 論文推薦 | 可用性 | 提供離線模式 |
| Google Scholar | 引用數 | 無官方 API | 用 Semantic Scholar 替代 |
| ORCID | 作者 h-index | Rate limit | 定期批次更新 |

### 資料品質

- **掠奪性期刊名單**：需要定期更新（Beall's List）
- **Impact Factor**：資料來源付費（Web of Science）
- **作者 h-index**：來源不統一（Google Scholar vs Scopus）

### LLM 成本

- **Persona 點評**：每篇論文 × 每個 persona = 大量 LLM 調用
- **文獻回顧生成**：長文本生成，token 消耗大

**緩解策略**：
- 快取點評結果
- 提供「簡化模式」（更短的 prompt）
- 支援本地 LLM（Ollama）

---

## 未來擴展

### 可能的功能

1. **社群協作**：
   - 分享 persona 定義
   - 共享文獻回顧模板
   - 眾包可信度評估

2. **自動化監控**：
   - 追蹤新論文（RSS, arXiv alerts）
   - 自動更新文獻回顧
   - 發現新的 gaps

3. **智能推薦**：
   - 基於閱讀歷史推薦論文
   - 識別相似研究者
   - 建議跨領域連結

4. **整合外部工具**：
   - Zotero 同步
   - Mendeley 匯入
   - Notion 整合

---

## 總結

這套進階功能系統將 Capsa 從「PDF 管理工具」提升為「智能學術研究助手」：

1. **可信度系統**：幫助研究者識別優質文獻
2. **Persona 系統**：提供多視角的深度解讀
3. **文獻回顧系統**：引導主動研究，識別並填補 gaps

**核心優勢**：
- ✅ 互動式、迭代式工作流
- ✅ 自動識別研究 gap
- ✅ 整合 LLM 和傳統檢索
- ✅ 完整的可追溯性（DuckDB + Wiki）

---

**本文件狀態**：設計階段，等待實作
**預計工作量**：7 週（3 個功能模組）
**關鍵依賴**：外部 API（CrossRef, Semantic Scholar, ORCID）
