## ADDED Requirements

### Requirement: PDF 頁面渲染為影像
系統 SHALL 將 PDF 的每一頁依設定 DPI（預設 300，環境變數 `OCR_DPI`）渲染為影像陣列，並依頁序回傳。

#### Scenario: 多頁 PDF
- **WHEN** 輸入一份 3 頁的 PDF
- **THEN** 系統回傳 3 張依頁序排列的影像

#### Scenario: 超過頁數上限
- **WHEN** PDF 頁數超過 `MAX_PAGES`
- **THEN** 系統僅處理前 `MAX_PAGES` 頁

#### Scenario: 無效的 PDF
- **WHEN** 輸入的位元組不是合法 PDF
- **THEN** 系統拋出 `InvalidPdfError`

### Requirement: OpenCV 影像前處理
系統 SHALL 以 OpenCV 將影像轉為灰階、去雜訊並以 Otsu 方法二值化，輸出單通道且僅含 0 與 255 的影像。

#### Scenario: 彩色影像前處理
- **WHEN** 輸入 3 通道彩色影像
- **THEN** 輸出為與原圖同寬高的單通道影像，像素值僅有 0 與 255

### Requirement: Tesseract 文字辨識並輸出文字行
系統 SHALL 使用 Tesseract（語言預設 `chi_tra+eng`，環境變數 `OCR_LANG`）辨識影像，將辨識出的字詞依 Tesseract 的 block/paragraph/line 編號聚合為「文字行」，再將同頁中垂直範圍重疊（重疊高度達較矮者 50%）的文字行合併為同一視覺列；文字行依由上而下排序、行內字詞依由左而右排序，並排除空白字詞與信心值小於 0 的項目。

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
