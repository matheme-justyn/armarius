# Armarius 這一版實作與 UIUX 修正拆解

> 對應主計劃：`docs/armarius-uiux-optimization-plan.md`

## 目標

這一版不追求全功能翻修，而是先把目前 `Streamlit` 版的主敘事、頁面角色與使用動線收斂正確。

## 實作與 UIUX 修正範圍

### 1. Dashboard 重構

**目的**：讓首頁成為研究控制台，而不是資訊堆疊頁。

**預計改動**：
- 重寫首頁 hero / summary 區塊
- 重新整理 metrics 與 next actions 的排序
- 弱化低價值系統資訊，改收進次要區塊
- 強化從 Dashboard 跳往 Library / Analysis / Synthesis 的入口

**主要檔案**：
- `armarius/app.py`
- 視需要補 `i18n` 文案

### 2. Library 頁重整

**目的**：讓 Library 明確是材料工作區。

**預計改動**：
- 重整 room 命名與頁首說明
- 清楚分層 intake / normalize / review / inventory
- 把次要 metadata 與低頻操作收進 expander 或 secondary section
- 提高表格與篩選的判讀性

**主要檔案**：
- `armarius/app.py`
- 視需要補 `i18n` 文案

### 3. Analysis 頁升級

**目的**：讓 Paradigm Analysis 從送出表單變成工作站。

**預計改動**：
- 新增頁首概念說明
- 補上前置條件與輸出說明
- 調整表單區與說明區的版面
- 補執行後的後續導引

**主要檔案**：
- `armarius/app.py`
- 視需要補 `i18n` 文案

### 4. Synthesis 頁升級

**目的**：讓 Concerto Synthesis 有明確的受眾輸出敘事。

**預計改動**：
- 新增 Concerto 概念說明
- 拆開 audience framing 與 deliverable expectation
- 補前置條件提示
- 補執行後導引文案

**主要檔案**：
- `armarius/app.py`
- 視需要補 `i18n` 文案

### 5. Guide 頁轉型

**目的**：讓 Guide 成為產品說明與操作地圖。

**預計改動**：
- 重寫 guide 摘要結構
- 將頁面用途、工作流、概念說明與 phase 限制整理成更可讀內容
- 對齊實際頁面結構

**主要檔案**：
- `armarius/app.py`
- `docs/workflow-guide.md`

### 6. UI/UX 細節修正

**目的**：把產品語言、視覺層級、互動回饋與版面節奏一起修正。

**預計改動**：
- 調整頁首標題、副標與說明文案
- 重新分配 metrics、actions、details 的視覺權重
- 把次要資訊收進 expander 或 secondary section
- 強化執行前後的引導與回饋
- 統一 Dashboard、Library、Analysis、Synthesis、Guide 的產品語言

**主要檔案**：
- `armarius/app.py`
- 視需要補 `i18n` 文案

### 7. 文件同步

**目的**：保持產品敘事與文件一致。

**預計改動**：
- 更新 `docs/web-sidebar-spec.md`
- 更新 `docs/workflow-guide.md`
- 視需要更新 `README.md`
- 記錄 `CHANGELOG.md`

## 不在這一版內

以下項目不放在這一版：

- React 化或改前後端架構
- citation graph 新視覺化
- argument engine
- 大型資料模型重整
- 新增複雜後端 pipeline

## 實作順序

1. 先改 `Dashboard` 與整體頁面敘事
2. 再改 `Library` 的資訊分層
3. 再改 `Analysis` / `Synthesis` 工作站化
4. 補 UI/UX 細節修正與文案層級
5. 再改 `Guide` 與文件同步
6. 最後做 smoke test / pytest / 啟動驗證

## 預期風險

- `armarius/app.py` 已較大，這一版可能需要先做局部重構才能安全修改
- 若 i18n key 分散，文案同步會比預期多
- 若現有測試對 UI 覆蓋低，驗證將以 smoke test 為主

## 完成標準

這一版完成時，至少應達成：

- 首頁能清楚表達產品定位、下一步與主要行動
- Library / Analysis / Synthesis / Guide 的角色與視覺層級更清楚
- Analysis / Synthesis 不再只是表單操作頁
- Guide 可以拿來當實際導覽頁
- 文件與 UI 主結構一致


## 補充：這一版已納入的頁面說明文

- 每個主要頁面都要先說明「這一步預期要做什麼」
- 頁面內文只描述目前產品真正已實作的能力
- 避免把長期 roadmap 或未完成能力寫得像已經可用
- 此調整對應本輪 UIUX / workflow / docs alignment 類 issue


## 補充：跨頁面共通資訊配置

- `目前工作區` 這類資訊屬於跨頁面共通狀態，不應佔用某一頁的主內容區
- 這一版已將工作區 path 與 workflow 狀態移到左側工作列底部
- 各頁主內容區只保留當頁步驟說明、可執行操作與必要結果
