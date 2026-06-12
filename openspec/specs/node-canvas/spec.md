# node-canvas Specification

## Purpose
TBD - created by archiving change redesign-ui-axon. Update Purpose after archive.
## Requirements
### Requirement: 藍圖網格節點畫布
系統 SHALL 提供自繪節點畫布，以青色藍圖網格為背景，將流程節點以垂直卡片流由上而下排列，相鄰節點間以連線連接。畫布 MUST NOT 依賴 NodeGraphQt。

#### Scenario: 節點垂直排列
- **WHEN** 載入含 N 個節點的流程
- **THEN** 畫布由上而下渲染 N 張節點卡，相鄰節點間顯示連線

#### Scenario: 藍圖網格背景
- **WHEN** 畫布渲染
- **THEN** 背景顯示青色網格線

### Requirement: 節點卡渲染
每張節點卡 SHALL 顯示分類圖示、節點序號、名稱、實例編號與狀態文字，並以狀態點呈現節點當前狀態（就緒/已選取/執行中/完成）。

#### Scenario: 節點卡內容
- **WHEN** 渲染一個節點卡
- **THEN** 卡片顯示該節點的圖示、序號、名稱與狀態文字

### Requirement: 節點選取
系統 SHALL 允許使用者點擊節點卡以選取之，被選取的節點 MUST 以高亮邊框呈現，且同一時間僅一個節點為選取狀態。

#### Scenario: 點擊選取節點
- **WHEN** 使用者點擊某節點卡
- **THEN** 該節點呈現選取高亮，先前選取的節點取消高亮

### Requirement: 執行點亮動畫
當流程執行時，系統 SHALL 依序點亮正在執行的節點，已完成節點以成功色標記，並在已執行的連線上呈現資料流動畫。

#### Scenario: 逐級點亮
- **WHEN** 流程執行進行中
- **THEN** 當前執行節點以高亮呈現，其上游已完成節點以成功色標記

### Requirement: 畫布縮放控制
系統 SHALL 在畫布左下角提供浮動控制條，顯示流程執行耗時並提供放大、縮小、重設縮放（100%）功能；縮放 MUST 實際縮放畫布上的節點。

#### Scenario: 放大縮小
- **WHEN** 使用者點擊放大或縮小
- **THEN** 畫布節點依對應比例縮放，且控制條顯示更新後的縮放百分比

#### Scenario: 重設縮放
- **WHEN** 使用者點擊縮放百分比
- **THEN** 縮放重設為 100%

