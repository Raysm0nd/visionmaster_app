## Why

現有桌面 UI 以 NodeGraphQt 通用節點編輯器 + 浮動 QDockWidget 拼湊而成，視覺零散、無法呈現品牌感。設計團隊已在 Claude Design 完成「AXON / VisionPower」設計稿並定案，採 AGC 企業配色與藍圖網格節點畫布。需將桌面 UI 重寫以對齊定案設計，並維持與既有引擎的完整連動。

## What Changes

- 以 PySide6 自訂 QWidget 重寫整個主視窗，達到設計稿像素級還原。
- **BREAKING**：移除 NodeGraphQt 依賴與 `graph_bridge.py` 的 NodeGraphQt 綁定；節點畫布改為自繪 widget。
- 新增無邊框視窗 + 自訂標題列（logo、選單、雲同步/設定/視窗控制鈕）。
- 新增工具列：儲存/開啟/另存/匯入/加密 + 擷取/模組庫/變數/3D/校正/腳本 + 「執行全部」「部分執行」按鈕。
- 新增左側 56px 圖示塢（12 類節點分類）。
- 新增自繪藍圖網格垂直節點卡畫布，含選取/執行點亮/資料流連線動畫、浮動縮放控制條。
- 右側 542px 面板：源圖 / 輸出結果分頁，含影像預覽（棋盤底、前後切換、掃描動畫）與結果鍵值表。
- 套用 AGC 配色（#0C4DA2 / #2F80D8 / #D23A55 / #34d399）與 Space Grotesk / IBM Plex Sans / JetBrains Mono 字型。
- 保留引擎連動：點節點顯示真實 PropertyPanel、執行呼叫真實 Scheduler、預覽顯示真實 OpenCV 影像、儲存/載入 JSON。

## Capabilities

### New Capabilities
- `desktop-shell`: 無邊框主視窗、自訂標題列、工具列、狀態列等外殼框架與視窗控制行為。
- `node-canvas`: 自繪藍圖網格節點畫布——節點卡渲染、選取、執行點亮動畫、連線資料流、縮放控制。
- `inspection-panels`: 右側源圖/輸出結果分頁、影像預覽（切換/掃描/讀數）與結果鍵值表、左側分類塢。

### Modified Capabilities
<!-- 無既有 spec；此前未以 OpenSpec 管理，故全為新增 -->

## Impact

- **修改/重寫**：`visionpower/app/main_window.py`、`graph_bridge.py`、`panels.py`、`preview_view.py`、`property_panel.py`、`theme.py`、`main.py`。
- **新增**：自繪畫布 widget、標題列/工具列/塢等元件模組、字型資源。
- **依賴**：`pyproject.toml` 移除 `NodeGraphQt`（保留 PySide6）。
- **引擎**：`visionpower/core/` 不受影響（維持無 Qt 解耦）。
- **測試**：既有 GUI 橋接測試需改寫；新增自繪畫布與外殼的離屏 pytest-qt 測試。
