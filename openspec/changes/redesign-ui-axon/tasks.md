## 1. 主題與資源基礎（無依賴）

- [x] 1.1 撰寫 `tests/test_app/test_theme.py`：驗證 `theme.py` 匯出 AGC 配色常數（AC/PRIMARY/RED/SUCCESS/BG…）與字型族常數，且字型缺失時有回退值
- [x] 1.2 重寫 `visionpower/app/theme.py`：具名顏色常數、字型族（Space Grotesk/IBM Plex Sans/JetBrains Mono + 回退）、產生 Qt StyleSheet 的輔助函式
- [x] 1.3 新增節點分類資料表（12 類：圖示鍵+中文名）與節點色票常數，集中於 `theme.py` 或 `app/constants.py`

## 2. 純資料橋（依賴 1）

- [x] 2.1 撰寫 `tests/test_app/test_graph_bridge.py`：驗證重寫後的 `GraphBridge` 維護有序核心節點清單、可新增/清除、`to_core_graph()` 產出可被 Scheduler 執行（無 Qt、無 NodeGraphQt）
- [x] 2.2 重寫 `visionpower/app/graph_bridge.py`：移除 NodeGraphQt 綁定，改為純資料橋（節點清單 + 顯示順序 + 對核心層介面）
- [x] 2.3 重寫示範流程建構函式：以資料橋建立 影像源→…→發送數據 的有序節點，供畫布與 Scheduler 使用

## 3. 視窗外殼 desktop-shell（依賴 1）

- [x] 3.1 撰寫 `tests/test_app/test_shell.py`（offscreen）：標題列顯示 logo/應用名/五選單；最大化↔還原切換；關閉鈕呼叫 close；工具列含執行全部/部分執行
- [x] 3.2 實作 `app/title_bar.py`：無邊框拖曳、logo、選單占位、雲同步/設定/最小/最大/關閉鈕
- [x] 3.3 實作 `app/toolbar.py`：檔案/模組動作圖示鈕 + 執行全部（主要）/部分執行（次要）按鈕，發出對應 signal
- [x] 3.4 實作 `MainWindow` 外殼骨架：`FramelessWindowHint`、grid 列高（46/54/body/30）、狀態列

## 4. 左塢與右面板 inspection-panels（依賴 1、3）

- [x] 4.1 撰寫 `tests/test_app/test_panels.py`（offscreen）：左塢渲染 12 分類且可選取高亮；右面板源圖/輸出結果分頁可切換；結果鍵值表依節點資料渲染
- [x] 4.2 實作 `app/dock.py`：左側 56px 圖示塢，分類選取高亮
- [x] 4.3 重寫 `app/preview_view.py`：棋盤底影像預覽、前/後切換、檔名+尺寸讀數、執行中掃描動畫覆蓋層
- [x] 4.4 重寫 `app/panels.py`：右側源圖/輸出結果分頁容器 + 子工具列（分割/網格/縮放/全螢幕）+ 輸出結果鍵值表
- [x] 4.5 重寫 `app/property_panel.py`：套用新主題，維持 `param_changed` signal 與既有節點參數連動

## 5. 自繪節點畫布 node-canvas（依賴 1、2）

- [ ] 5.1 撰寫 `tests/test_app/test_canvas.py`（offscreen）：節點命中測試→選取狀態、單一選取、縮放數值（放大/縮小/重設 100%）、執行狀態機（running/ranStep/runFrom）逐級推進
- [ ] 5.2 實作 `app/canvas.py` 繪製層：QPainter 藍圖網格背景、垂直節點卡（圖示/序號/名稱/狀態點）、節點間連線
- [ ] 5.3 實作畫布互動：`mousePressEvent` 命中選取（發 signal）、`painter.scale` 縮放、浮動控制條（耗時+放大/縮小/重設）
- [ ] 5.4 實作執行動畫：`QTimer` 320ms/級逐級點亮、完成標記、連線資料流動畫

## 6. 引擎連動整合與收尾（依賴 2、3、4、5）

- [ ] 6.1 撰寫 `tests/test_app/test_main_window.py`（offscreen）：選取節點→PropertyPanel 顯示真實參數；執行全部/部分執行→呼叫 Scheduler 並更新預覽/結果；儲存/載入 JSON
- [ ] 6.2 重寫 `MainWindow` 連動：畫布選取↔屬性/預覽/結果；執行按鈕↔Scheduler + 畫布動畫；參數修改→增量重算
- [ ] 6.3 接上儲存/載入 JSON 流程與 `main.py` 入口；確認 `/run-app` 可啟動
- [ ] 6.4 `pyproject.toml` 移除 NodeGraphQt 依賴；全專案搜尋確認無殘留 import
- [ ] 6.5 跑 `QT_QPA_PLATFORM=offscreen uv run pytest` 全綠 + `/gui-verify` 離屏截圖比對設計稿；ruff lint 通過
