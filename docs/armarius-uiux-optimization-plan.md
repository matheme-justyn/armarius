# Armarius 真實設計與 UIUX 優化計劃書

> 日期：2026-06-23  
> 狀態：Draft / 待確認後實作

## 1. 背景與目的

這份計劃書的目的，是把 `kb-armarius` 中較成熟的產品設計，與 `matheme-lib` 已實際試用後反映出的 UX 經驗，收斂回 `tool-armarius`／`armarius` 套件本體，讓目前已存在的 Streamlit 版產品，不只是「功能可用」，而是更接近真正可持續使用的研究工作台。

本次工作先不直接擴張底層能力邊界，而是優先修正以下問題：

- 現況 UI 雖已有多頁結構，但主敘事仍偏向工程流程與房間切換，對研究者的任務心智模型不夠直接。
- `kb-armarius` 的產品概念已經更清楚區分 `Library / Analysis / Synthesis / Guide / Settings`，但 `tool-armarius` 仍有部分資訊架構、命名與頁面內容沒有完全對齊。
- `matheme-lib` 的實際使用脈絡顯示：使用者更在意「現在手上有哪些材料、下一步能做什麼、目前輸出值不值得信任」，而不是先看到大量配置與流程名詞。
- 現有 Streamlit UI 已具備 Phase 0/1 的主要骨架，因此最有效率的策略不是重寫，而是做一次產品層重整：資訊架構、頁面敘事、互動細節、視覺層級、文案與導引同步優化。

## 2. 依據來源

本計劃書主要根據以下三條來源綜合整理：

### 2.1 `kb-armarius` 的最新設計方向

從 `kb-armarius/armarius/docs/PRD.md` 與 `kb-armarius/armarius/docs/gui-paradigm-specification.md` 可抽出幾個重要方向：

- Armarius 應是「從 PDF 到知識卡、再到觀點分析與綜整」的研究工作台。
- 使用者的主要工作流不是抽象功能清單，而是：
  1. 收進文獻
  2. 建立可閱讀與可評估的摘要
  3. 套用 Paradigm 做多角度分析
  4. 透過 Concerto 針對不同受眾輸出成果
- `Paradigm` 與 `Concerto` 是面向使用者的概念，應該被當作理解研究工作的產品語言，而不是只當成技術模組名。
- Dashboard / Library / Analysis / Synthesis / Guide / Settings 的頁面分工應該清楚，不應在側欄或首頁混放太多設定與低價值控制。

### 2.2 `tool-armarius` 現有實作現況

根據 `tool-armarius/armarius/app.py`、`tool-armarius/docs/web-sidebar-spec.md` 與 `tool-armarius/docs/merge-roadmap/DESIGN_VS_REALITY.md`：

- 目前已有 dedicated pages 與較乾淨的 sidebar 方向，這是正確基礎。
- 但整體仍偏「系統操作面板」，對新使用者來說比較像 admin/debug app，而不是研究工作台。
- Library 頁有大量工作流房間（room）與資料檢視，但任務導向不足。
- Analysis / Synthesis 頁面已有獨立入口，但仍偏表單式操作，少了「為什麼要做這一步、做完會得到什麼」的上下文。
- Settings 已拆頁，方向正確，但仍需與主工作流更清楚切分。

### 2.3 `matheme-lib` 試用經驗的可遷移原則

雖然 `matheme-lib` 不一定是一個完整 UI 專案，但從其實際使用脈絡，可以提煉出適合移植到 Armarius 的產品原則：

- 使用者需要先看到「成果物」與「可採取行動」，再看技術細節。
- 對知識工作產品來說，好的 UX 不是塞更多功能，而是讓使用者快速判斷：
  - 我現在在哪個研究階段？
  - 哪些資料可用？
  - 哪些東西有風險、需要補強？
  - 下一步最值得做的是什麼？
- 同一頁內若混入太多設定、狀態、表單、原始資料與次要細節，會讓使用者失去焦點。
- 真正有價值的介面應該把「主結果」、「可追溯證據」、「次要細節」分層，而不是全部平鋪。

## 3. 問題定義

綜合上面三條來源，目前 `tool-armarius` 在真實設計與 UIUX 上的主要問題如下：

### 3.1 產品主敘事仍不夠清楚

目前有頁面，但缺少一條清楚的產品主線：

- Armarius 到底是 library browser？
- 是 PDF 處理器？
- 是 paradigm analysis 工具？
- 是 synthesis workbench？

答案其實是「研究工作台」，但這個概念在目前 UI 中還沒有被清楚地表現出來。

### 3.2 Library 與 Dashboard 的界線仍可再拉開

依照 `web-sidebar-spec.md`，Dashboard 應該負責總覽、隊列、提醒、下一步；Library 應該是執行工作區。

目前實作雖已朝這方向前進，但還可以更明確：

- Dashboard 應更偏「決策入口」
- Library 應更偏「材料管理與處理」
- 次要狀態與原始資訊應該被收進次層，而不是占據主要畫面注意力

### 3.3 Analysis / Synthesis 缺少結果導向敘事

現在的獨立頁面偏向「填表單 -> 送出」，但對使用者來說，重要的是：

- 這個 Paradigm 會從哪些角度分析？
- 選這個 Concerto 代表我要產出給誰看？
- 執行後會得到什麼型態的輸出？
- 我應該先整理哪些材料再來做這步？

換句話說，目前操作存在，但任務上下文不足。

### 3.4 Guide/Tutorial 與實際工作流的接縫還不夠好

Guide 現在比較像說明頁，但若要成為真正有用的 onboarding 與持續使用輔助，它應該：

- 解釋 Armarius 的工作模型
- 清楚告訴使用者何時該去哪一頁
- 幫助使用者理解 Paradigm / Concerto 這些產品概念
- 成為從「第一次使用」到「遇到卡點」都可回來看的操作地圖

### 3.5 UI 層級與文案可讀性仍有提升空間

目前畫面中，以下問題仍容易發生：

- 指標、清單、表格、控制元件的視覺權重過於接近
- 表單與結果區塊沒有明顯分層
- 一些功能命名偏內部實作視角
- 頁面上的「下一步」提示不夠穩定

## 4. 本次優化目標

本次優化鎖定在「不大改底層架構、不切換前端框架」前提下，將 Streamlit 版 Armarius 收斂成更像真正產品的 v1.5 版本。

### 4.1 核心目標

1. **重新對齊產品主敘事**：明確把 Armarius 呈現為 research workspace，而不是功能集合。
2. **強化資訊架構**：讓 Dashboard / Library / Analysis / Synthesis / Guide / Settings 各自角色更穩定。
3. **優化任務導向 UX**：每個主要頁面都能回答「我在這裡能做什麼、為什麼現在要做、做完得到什麼」。
4. **把細節分層**：主結果優先、次要資訊收納、避免 debug 感過重。
5. **補齊文件同步**：讓 PRD、側欄規格、工作流說明與實際 UI 一致。

### 4.2 非目標

這次不做以下事項，避免範圍失控：

- 不切換到 React / FastAPI 前後端分離
- 不新增大型新能力（例如 argument engine、citation graph 視覺化）
- 不重寫資料庫層
- 不擴張成多工作區管理產品
- 不處理與本次 UIUX 主題無關的底層理想架構缺口

## 5. 設計原則

本次實作會遵守以下原則：

### 5.1 Workflow first, not feature first

每個頁面都應先對應研究階段與使用者任務，而不是對應程式模組。

### 5.2 Result first, detail second

先呈現最有價值的結果、摘要、推薦動作，再把細節放進 expander、secondary section 或表格。

### 5.3 Explain the why, not only the how

Analysis / Synthesis / Guide 不只提供操作元件，也要解釋該步驟的目的與輸出。

### 5.4 Stable language for product concepts

`Paradigm`、`Concerto`、`Library`、`Guide` 等概念要穩定使用，不混入太多內部術語。

### 5.5 Progressive disclosure

讓進階資訊可取得，但不干擾主畫面。高頻任務優先，低頻設定收斂。

## 6. 建議實作範圍

以下是待確認後的建議實作項目。

### 6.1 Dashboard 重構為真正的「研究控制台」

**目標**：把 Dashboard 做成使用者進入 app 後最容易理解現況與下一步的地方。

**調整方向**：

- 首屏展示研究工作台定位與目前 library 狀態
- 用較清楚的摘要卡呈現：文獻量、可讀性、待處理項、可分析項
- 強化 next actions 區塊，讓使用者知道接下來應去 Library、Analysis 或 Synthesis
- 將低價值系統細節下沉，不作為首頁主內容

### 6.2 Library 頁重整為「材料工作區」

**目標**：讓 Library 專注於文獻材料的收件、檢視、篩選與基本處理。

**調整方向**：

- 弱化 room 切換的心智負擔，改強調目前是材料管理工作區
- 更清楚區分：
  - intake / normalization / catalog review / library inventory
- 將原始紀錄、進階 metadata、次要操作收進次層
- 表格與篩選設計優先支援「快速判讀有哪些材料值得下一步處理」

### 6.3 Analysis 頁升級為「Paradigm 工作站」

**目標**：讓 Analysis 頁從單純表單變成任務導向頁面。

**調整方向**：

- 補上頁首說明：什麼是 Paradigm、何時該做這步
- 在選擇 paradigms 前，先顯示可分析前提與推薦條件
- 將輸入表單與預期輸出分欄或分區呈現
- 強化執行後回饋訊息，讓使用者知道後續應去哪裡看成果

### 6.4 Synthesis 頁升級為「Concerto 產出工作站」

**目標**：讓使用者理解 Concerto 不只是 another form，而是針對不同受眾編排研究成果的階段。

**調整方向**：

- 補上頁首概念說明與例子
- 將 paradigm filter、concerto 選擇、輸出說明分開呈現
- 用更清楚的文案說明會產生什麼形式的成果
- 加上前置條件提醒，避免在資料不足時直接操作

### 6.5 Guide/Tutorial 轉型為「產品說明 + 操作地圖」

**目標**：讓 Guide 成為長期有用的說明頁，而不只是一次性教學。

**調整方向**：

- 用產品語言解釋 Armarius 的完整研究工作流
- 明確對應各頁用途與使用時機
- 補上 Paradigm / Concerto 概念導讀
- 說明目前 Phase 1 能做什麼、哪些能力仍未完成

### 6.6 文案、命名、層級與空白優化

**目標**：提升整體可讀性與產品感。

**調整方向**：

- 統一頁面標題、副標、區塊命名
- 增加 section-level 的說明與行動提示
- 減少首頁與主頁過度密集的 debug/狀態訊息
- 強化 metrics、actions、data table、details 之間的視覺層級

### 6.7 文件同步

**目標**：避免文件與 UI 再次分離。

**待更新文件**：

- `docs/web-sidebar-spec.md`
- `docs/workflow-guide.md`
- `README.md`
- 視必要更新 `docs/PRD.md` 中 Web UI v1 的實際描述
- `CHANGELOG.md`

## 7. 預計交付物

待你確認後，我預計交付以下成果：

1. **UI 重構實作**：更新 `armarius/app.py` 的頁面結構、文案與互動層次
2. **必要 i18n 同步**：補齊相關文案 key（至少 en-US / zh-TW）
3. **文件更新**：同步 workflow、sidebar、README、changelog
4. **驗證結果**：至少完成
   - `pytest` 相關測試（若現有測試可跑）
   - 基本啟動/匯入驗證
   - 針對 UI 主要流程的靜態檢查或 smoke test

## 8. 實作策略

若你確認這份計劃書，建議依以下順序實作：

1. 先整理頁面資訊架構與區塊順序
2. 再改頁面文案與概念說明
3. 再調整主要操作區塊與次要資訊收納
4. 最後同步 i18n 與文件
5. 收尾做 smoke test / pytest / 基本啟動驗證

## 9. 驗收標準

這次優化完成後，應至少達成以下狀態：

- 使用者進入首頁後，能在短時間內理解 Armarius 是什麼、現在資料庫狀態如何、下一步該去哪裡。
- Library / Analysis / Synthesis / Guide / Settings 的角色更清楚，不再像一組鬆散頁面。
- Analysis 與 Synthesis 不再只是裸表單，而有清楚任務脈絡與結果導向敘事。
- Guide 能作為實際可用的工作流地圖。
- 現有 Streamlit UI 的 debug/admin 感下降，產品感提升。
- 文件與實作至少在主要頁面結構與敘事上保持一致。

## 10. 我目前採用的合理假設

在你尚未補充更多限制前，我先採用以下假設：

1. 這次優先優化的是 `tool-armarius` 現有 Streamlit UI，而不是另起新前端。
2. `kb-armarius` 提供的是產品目標與設計方向，不要求逐字逐頁完全照搬。
3. `matheme-lib` 在這次任務中主要作為 UX 經驗來源，而不是要直接抽取可運行元件。
4. 可以接受對現有頁面文案、區塊排序、說明方式、互動分層做較明顯調整，只要不破壞既有核心功能。
5. 若文件描述與現有程式行為不一致，會以「讓產品更可交付」為優先進行收斂。

---

如果你認可這份方向，我下一步就會依這份計劃書直接開始實作，不再拆很多回合確認。
