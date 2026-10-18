# excel-export Specification

## Purpose
TBD - created by archiving change add-pdf-ocr-extractor. Update Purpose after archive.
## Requirements
### Requirement: 擷取結果輸出為 Excel
系統 SHALL 將擷取結果輸出為 `.xlsx`，工作表名稱為 `擷取結果`；第一列為標頭 `檔名` 加上依使用者順序排列的標題；每份 PDF 佔一列。

#### Scenario: 兩份 PDF 兩個標題
- **WHEN** 標題為 `工程編號`、`日期`，結果有 `a.pdf`（`A1`、`2026/10/16`）與 `b.pdf`（`B2`、空字串）
- **THEN** Excel 第 1 列為 `檔名, 工程編號, 日期`，第 2 列為 `a.pdf, A1, 2026/10/16`，第 3 列為 `b.pdf, B2,`（空白儲存格）

#### Scenario: 標頭格式
- **WHEN** 產生 Excel
- **THEN** 標頭列為粗體且凍結首列

#### Scenario: 值以文字型態保存
- **WHEN** 擷取值為 `00123`
- **THEN** Excel 儲存格內容為文字 `00123`，不被轉為數字

