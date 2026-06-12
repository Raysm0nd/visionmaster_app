## Context

現有 `visionpower/app/` 以 NodeGraphQt 提供節點畫布，並用多個 `QDockWidget` 拼出面板。設計稿（AXON / VisionPower）要求像素級的自訂外殼：無邊框視窗、自訂標題列/工具列、左側 56px 圖示塢、自繪藍圖網格垂直節點卡畫布、542px 右側分頁面板、浮動縮放控制條。引擎層（`visionpower/core/`）為純 Python 無 Qt，須維持解耦不動。

設計稿原型是 HTML/CSS/JS（React 風格、6 個寫死節點、SVG 假圖）。本設計取其視覺與互動，但接回真實引擎（Scheduler、真實節點、OpenCV 影像）。

設計稿關鍵數值：視窗 1440×902，列高 標題46 / 工具列54 / body / 狀態列30；body 欄寬 左塢56 / 畫布1fr / 右面板542。配色 #05070b 底、AGC 深藍 #0C4DA2、互動 #2F80D8、紅 #D23A55、綠 #34d399。節點色：影像源#2dd4bf、快速匹配#5aa0e6、BLOB#a78bfa、字元辨識#fbbf24、格式化#f472b6、發送數據#34d399。

## Goals / Non-Goals

**Goals:**
- 以 PySide6 自訂 QWidget 像素級還原設計稿的版面、配色、字型與互動。
- 移除 NodeGraphQt，改用 `QWidget` + `QPainter` 自繪節點畫布。
- 維持與真實引擎連動：選取→PropertyPanel、執行全部/部分執行→Scheduler、預覽→OpenCV、儲存/載入→JSON。
- 元件化：標題列、工具列、左塢、畫布、右面板各自獨立模組，可離屏 pytest-qt 測試。

**Non-Goals:**
- 不改動 `visionpower/core/`（引擎契約不變）。
- 不實作設計稿提及但非定案的「外觀方案切換」（已固定技術藍圖）。
- 不實作拖拽連線建流程（保留 demo 流程建構；本次聚焦視覺重寫與既有連動）。
- 不處理 M2 模型節點。

## Decisions

**D1：自繪畫布用 QWidget + QPainter，而非 QGraphicsScene。**
節點為固定垂直流、數量少（個位數），版面單純。QPainter 直接繪製網格背景、卡片、連線最直接，且容易做執行點亮/資料流動畫與縮放（`painter.scale`）。替代方案 QGraphicsScene 功能過剩、樣板碼多；NodeGraphQt 已確認無法產生藍圖外觀。互動以 `mousePressEvent` 命中測試節點矩形即可。

**D2：無邊框視窗以 `Qt.FramelessWindowHint` + 自訂標題列實作拖曳與視窗控制。**
標題列攔截 `mousePress/mouseMove` 做視窗移動，控制鈕呼叫 `showMinimized/showMaximized/showNormal/close`。替代方案（保留原生標題列）無法達成設計稿外觀，故排除。

**D3：樣式集中於 `theme.py`，匯出顏色常數 + 產生 Qt StyleSheet 字串。**
所有顏色/字型以具名常數定義，元件引用常數而非硬編碼色碼（呼應 Karpathy「不硬編碼魔法數字」與專案 lint 要求）。字型 Space Grotesk/IBM Plex Sans/JetBrains Mono 若系統無安裝則回退 sans-serif/monospace，不阻斷啟動。

**D4：節點分類塢與畫布節點解耦。**
左塢 12 分類為靜態資料表（圖示+名稱），點擊僅切換選取高亮（對齊設計稿行為）；不在本次綁定「點分類新增節點」邏輯，避免超出範圍。

**D5：保留 `GraphBridge` 概念但移除 NodeGraphQt 綁定。**
重寫為純資料橋：維護核心節點清單與其顯示順序，供畫布渲染與 Scheduler 執行；`to_core_graph()` 等對核心層的介面盡量沿用，降低對 `main_window` 執行邏輯的衝擊。

**D6：執行動畫用 `QTimer` 逐級推進。**
對齊設計稿 320ms/級的節奏，狀態機（running/ranStep/runFrom）驅動節點狀態與連線動畫；真實 Scheduler 在動畫起點一次算完結果，動畫僅呈現逐級點亮，避免阻塞 UI。

## Risks / Trade-offs

- **字型缺失** → 設計稿指定的 Google Fonts 在 Windows 未必安裝 → 提供回退字族；視覺略有差異但不影響功能。
- **像素級還原與 DPI 縮放衝突** → 高 DPI 下固定 px 版面可能偏移 → 以相對佈局（QLayout + 固定關鍵尺寸）而非絕對定位，關鍵欄寬（56/542）用固定值，其餘彈性。
- **移除 NodeGraphQt 為 BREAKING** → 既有 GUI 橋接測試會失效 → 改寫測試對應新自繪畫布；`pyproject.toml` 移除依賴。
- **自繪畫布的可測試性** → QPainter 繪製不易斷言像素 → 測試聚焦於狀態邏輯（命中測試、選取狀態、縮放數值、執行狀態機）與 widget 可建構性，而非像素比對。
- **一次大改的回歸風險** → 分階段實作（外殼→塢/面板→畫布→引擎連動），每階段以 `/gui-verify` 離屏截圖驗證，並維持 `git` 分支可回溯。

## Migration Plan

1. 於 `feature/axon-ui-redesign` 分支實作，主分支保持可用。
2. 依 tasks.md 分階段；每階段跑 `QT_QPA_PLATFORM=offscreen uv run pytest` 與 `/gui-verify`。
3. 全部通過後合併；`pyproject.toml` 移除 NodeGraphQt 於最終階段，確認無殘留 import。

## Open Questions

- 標題列選單（檔案/設定…）是否需展開實際下拉選項，或本次僅做視覺占位？（暫定：視覺占位 + 既有動作掛在工具列，待使用者確認再擴充）
- 左塢分類點擊未來是否要綁定新增對應節點？（暫列 Non-Goal）
