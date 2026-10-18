## MODIFIED Requirements

### Requirement: Tesseract 文字辨識並輸出文字行
系統 SHALL 使用 Tesseract（語言預設 `chi_tra`，環境變數 `OCR_LANG`）辨識影像。表格儲存格 SHALL 逐格辨識：依墨點範圍緊貼裁切並加白邊後以單行模式辨識，產生的字詞座標為儲存格矩形並標記為表格內字詞；空白儲存格不產生字詞。非表格區域 SHALL 在框線與儲存格塗白後整頁辨識，字詞依 Tesseract 的 block/paragraph/line 編號聚合。所有文字行再將同頁中垂直範圍重疊（重疊高度達較矮者 50%）者合併為同一視覺列；文字行依由上而下排序、行內字詞依由左而右排序，並排除空白字詞與信心值小於 0 的項目。

#### Scenario: 聚合字詞為文字行
- **WHEN** Tesseract 回傳同一 line 編號的字詞 `工程編號：` 與 `nglc5zxxxd`
- **THEN** 系統產出一個文字行，依左至右順序包含這兩個字詞

#### Scenario: 合併不同區塊但同一列的文字
- **WHEN** Tesseract 將 `工程編號` 與 `nglc5zxxxd` 辨識為不同 block，但兩者垂直位置相同
- **THEN** 系統產出一個文字行，依序包含 `工程編號` 與 `nglc5zxxxd`

#### Scenario: 排除空字詞
- **WHEN** Tesseract 回傳文字為空白或信心值為 -1 的項目
- **THEN** 該項目不出現在任何文字行中

#### Scenario: 真實影像辨識
- **WHEN** 輸入一張印有「工程編號：nglc5zxxxd」的清晰影像
- **THEN** 辨識結果的文字行中包含 `nglc5zxxxd`

#### Scenario: 同一表格列的儲存格合併為一行
- **WHEN** 表格某列有儲存格 `2`、`王小明`
- **THEN** 系統產出一個文字行，依序包含 `2`、`王小明`，且兩者皆標記為表格內字詞、座標為儲存格矩形

#### Scenario: 真實表格辨識
- **WHEN** 輸入名冊版型 PDF（表格跨頁、姓名欄含 `王小明`、`林志玲`、`趙六安`）
- **THEN** 辨識結果包含所有姓名，且中文姓名不被辨識為英文
