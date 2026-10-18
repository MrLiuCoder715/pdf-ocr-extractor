## MODIFIED Requirements

### Requirement: 擷取標題自由新增與刪除
介面 SHALL 顯示擷取標題清單（預設含 `工程編號`），使用者可輸入文字新增標題、刪除既有標題，並可將每個標題切換為「欄位」或「表格欄」模式（新增時預設為「欄位」）；空白或重複的標題不得加入；清單與模式保存於瀏覽器，重新整理頁面後仍保留；舊版只含標題文字的保存資料 SHALL 自動視為「欄位」模式。

#### Scenario: 新增標題
- **WHEN** 使用者輸入 `日期` 並按下「新增」
- **THEN** 標題清單顯示 `工程編號` 與 `日期`

#### Scenario: 拒絕重複標題
- **WHEN** 使用者輸入已存在的 `工程編號` 並按下「新增」
- **THEN** 清單不變並顯示提示訊息

#### Scenario: 刪除標題
- **WHEN** 使用者按下 `日期` 旁的刪除按鈕
- **THEN** `日期` 從清單中移除

#### Scenario: 重新整理後保留
- **WHEN** 使用者新增 `日期` 後重新整理頁面
- **THEN** 清單仍包含 `日期`

#### Scenario: 切換為表格欄
- **WHEN** 使用者按下 `姓名` 的模式按鈕
- **THEN** `姓名` 顯示為「表格欄」模式，重新整理後仍為「表格欄」

### Requirement: 匯入 PDF 並擷取
介面 SHALL 允許使用者選擇一或多個 PDF 檔並執行擷取，處理中顯示進行狀態，完成後以表格預覽結果，預覽內容與 Excel 輸出的列完全相同（含表格欄一筆一列的展開）。

#### Scenario: 擷取成功
- **WHEN** 使用者選擇一份含 `工程編號：nglc5zxxxd` 的 PDF 並按下「開始擷取」
- **THEN** 預覽表格顯示該檔名及 `工程編號` 欄值 `nglc5zxxxd`

#### Scenario: 未選擇檔案或無標題
- **WHEN** 使用者未選擇 PDF 或標題清單為空就按下「開始擷取」
- **THEN** 介面顯示錯誤提示且不送出請求

#### Scenario: 表格欄預覽
- **WHEN** 使用者將 `姓名` 設為表格欄並擷取名冊 PDF
- **THEN** 預覽表格每位姓名各佔一列

### Requirement: 擷取 API 輸入驗證
`POST /api/extract` SHALL 拒絕不合法的請求並回傳 HTTP 400 與 JSON 錯誤訊息：未附檔案、無標題、檔案非 PDF（副檔名或 `%PDF-` 檔頭不符）；超過 `MAX_UPLOAD_MB` 時回傳 HTTP 413。可重複的 `column_titles` 欄位指定表格欄，不在 `titles` 中的項目 SHALL 被忽略。成功回應 SHALL 包含 `titles`、`column_titles`、`results`（每項含 `filename`、`fields`、`rows`）與 `table`（`header`、`rows`，與 Excel 內容相同）。

#### Scenario: 上傳非 PDF
- **WHEN** 上傳 `note.txt`
- **THEN** 回應為 HTTP 400，JSON 含 `error` 欄位

#### Scenario: 合法請求
- **WHEN** 上傳一份 PDF 並帶標題 `工程編號`
- **THEN** 回應為 HTTP 200，JSON 包含 `titles` 與 `results`，`results[0].filename` 為上傳檔名

#### Scenario: 指定表格欄
- **WHEN** 標題為 `承商名稱`、`姓名`，`column_titles` 為 `姓名`、`不存在`
- **THEN** 回應的 `column_titles` 為 `["姓名"]`，且 `table.rows` 依姓名展開

### Requirement: Excel 匯出 API
`POST /api/export` SHALL 接收 JSON `{titles, column_titles, results}`（`column_titles` 可省略，`results` 每項的 `rows` 可省略）並回傳 `.xlsx` 檔（`Content-Disposition: attachment`）；格式錯誤時回傳 HTTP 400。

#### Scenario: 匯出成功
- **WHEN** 送出合法的 `{titles, results}`
- **THEN** 回應為 HTTP 200，內容類型為 xlsx 且可被 openpyxl 開啟

#### Scenario: 匯出表格欄
- **WHEN** 送出含 `column_titles: ["姓名"]` 與兩列 `rows` 的結果
- **THEN** Excel 為該 PDF 輸出兩列
