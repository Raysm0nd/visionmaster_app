# VisionPower

工廠產線用的**影像處理與瑕疵檢測平台**，採用節點式低程式碼工作流程編輯器。在藍圖畫布上**連接節點**即可建構檢測流程（目前為 OpenCV，下一步支援 CPU 模型），可即時預覽調參，並以 JSON 儲存/載入工作流程。

桌面介面採用 **AXON** 設計語言：無邊框深色視窗、AGC 企業配色（深藍 `#0C4DA2`／青色強調 `#2F80D8`／紅 `#D23A55`）、自繪藍圖節點畫布，以及自訂標題列／工具列／左側圖示塢／右側檢視面板——全部以 PySide6 直接打造，**不依賴 NodeGraphQt**。

![VisionPower — AXON UI](docs/screenshot.png)

## 架構

核心原則是**引擎/UI 解耦**：工作流程引擎為純 Python、**零 Qt 依賴**，可無頭執行（批次／產線服務）並完整單元測試。UI、未來的無頭服務、未來的 LLM/agent 層，都只是同一個引擎的使用者。

```
 app (PySide6 UI — 無邊框外殼 + 自繪畫布)
 ─────────────────────────────────────────────────────────────────────────
 nodes   (OpenCV／模型／IO 節點實作)
 ─────────────────────────────────────────────────────────────────────────
 core    (純 Python，無 Qt)
   types · ports · params · node · registry · graph · scheduler · serialize · inference
```

核心概念：
- **自描述節點**：每個節點宣告型別化的 ports 與 `ParamSpec`。同一份 schema 同時驅動節點卡、自動產生的屬性面板、連線型別驗證，以及未來的 LLM 層（`core.node_schema()`）。
- **增量快取**：排程器以「參數＋上游簽章」為每個節點簽名；改一個參數只重算該節點與其下游，其餘命中快取（即時調參）。
- **逐節點錯誤隔離**：單一節點失敗會被回報而非中斷；其下游節點略過。
- **純資料 UI 橋**：`GraphBridge` 維護有序的核心節點清單，按需重建可執行的 `core.Graph`——UI 框架不滲入引擎，畫布只是這份資料的其中一種呈現方式。

### 目錄結構
- [visionpower/core/](visionpower/core/) — 引擎（無 Qt）
- [visionpower/nodes/](visionpower/nodes/) — 內建 OpenCV 節點
- [visionpower/render.py](visionpower/render.py) — 疊圖／顯示輔助（OpenCV，無 Qt）
- [visionpower/app/](visionpower/app/) — PySide6 桌面 UI
  - `theme` · `constants` · `icons` — AGC 配色、版面尺寸、線性圖示工廠（QtSvg）
  - `title_bar` · `toolbar` · `dock` — 無邊框外殼 + 左側分類塢
  - `canvas` — 自繪藍圖節點畫布（QPainter）
  - `panels` · `preview_view` · `property_panel` — 右側 源圖／輸出結果／屬性 分頁
  - `graph_bridge` · `demo_flow` — 與引擎連接的純 Python 橋
  - `main_window` — 組裝外殼並接上真實引擎
- [tests/](tests/) — 引擎測試 + 無頭（offscreen）UI 測試

## 安裝與執行

```bash
uv sync                       # 核心引擎 + 測試（無 Qt）
uv sync --extra gui           # 加裝桌面 UI（PySide6 + QtSvg）
uv run python main.py         # 啟動應用（或：uv run visionpower）
```

啟動後畫布上已載入範例流程：
`ImageSource → Grayscale → GaussianBlur → Threshold → FindContours → Viewer`。

- **執行全部**：跑完整流程；節點逐級點亮，執行時源圖會出現掃描動畫。
- **部分執行**：從選取的節點往下執行。
- 點任一節點即可在 **屬性** 分頁編輯真實參數，並在 **源圖** 看其影像輸出、在 **輸出結果** 看結構化結果。
- 修改參數會增量重算（只重算受影響的節點）。
- 畫布左下角的浮動控制條顯示流程耗時與縮放。
- **儲存／載入**：以 JSON 保存工作流程。

視窗控制：自訂標題列提供最小化／最大化／關閉；拖曳標題列可移動視窗，從右下角把手可縮放。

## 測試

```bash
uv run pytest                                          # 引擎測試（無 Qt）
uv sync --extra gui --group gui-dev
QT_QPA_PLATFORM=offscreen uv run pytest                # + 無頭 UI 測試
```

## 開發藍圖
- **M1（完成）** — 引擎 + OpenCV 節點 + 節點編輯器 + 預覽 + 儲存/載入。
- **M1.5（完成）** — VisionMaster 風格 UI：ImageSource 資料夾節點 + 批次執行。
- **AXON UI（完成）** — 無邊框重新設計：AGC 配色 + 自繪藍圖畫布，移除 NodeGraphQt，保留引擎連動。
- **M2** — 透過 `InferenceBackend` 的模型節點（Intel CPU 上的 OpenVINO；ONNX 備援）。
- **M3** — NAS／資料夾來源 + 監看佇列 + 平行批次 + 結果匯出。
- **M4** — 無人值守產線部署的無頭服務。
- **M5** — LLM/agent 協助流程設計與參數建議。

專案專屬的 Claude Code 技能位於 [.claude/skills/](.claude/skills/)：`scaffold-node`、`run-app`、`gui-verify`。所有變更以 OpenSpec 追蹤（見 [openspec/](openspec/)）。
