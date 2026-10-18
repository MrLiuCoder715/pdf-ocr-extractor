## Why

使用者以實際文件（施工人員名冊）測試時，需要擷取「姓名」欄下的**所有**姓名，但輸出為空白。診斷結果：
1. Tesseract 預設版面分析會略過有框線的表格，表格內文字（含跨頁的後續表格）完全沒有被辨識。
2. `chi_tra+eng` 組合模型會把部分中文姓名誤判為英文（如 `林志玲` → `MEK`）；單用 `chi_tra` 即可正確辨識，且英數字不受影響。
3. 現有擷取邏輯只取「標題右側同一行的第一個值」，無法處理「欄位標頭下方多列資料」的表格。
4. 「同行無值時取下一行」規則在值為空白時會誤抓下一行的其他標籤（`工程編號` → `契約編號21915A451`）。

## What Changes

- **OpenCV 表格偵測**：以形態學運算找出表格框線與儲存格，逐格裁切後交給 Tesseract 辨識；非表格區域則在遮蔽表格後整頁辨識。
- **預設 OCR 語言改為 `chi_tra`**。
- **新增「表格欄」擷取模式**：標題可設為「表格欄」，系統擷取該欄標頭下方（含後續頁面）的每一列資料。
- **BREAKING**：移除「同行無值時取下一行」規則；標題右側無值時結果為空字串。
- 擷取值去除開頭的雜訊標點（`。`、`、`、`“`、`”` 等）。
- **Excel 一筆一列**：有表格欄時，每個表格列輸出一列，一般欄位值在每列重複；無表格欄時維持每份 PDF 一列。
- 介面：每個標題可切換「欄位／表格欄」模式；預覽表格與 Excel 內容一致。
- API：`/api/extract` 新增 `column_titles` 欄位；回應新增 `column_titles` 與每份結果的 `rows`。

## Capabilities

### New Capabilities
- `table-detection`: 以 OpenCV 偵測頁面中的表格框線與儲存格位置。

### Modified Capabilities
- `pdf-ocr`: 文字行來源改為「遮蔽表格後的整頁辨識 + 逐格辨識」，預設語言改為 `chi_tra`。
- `field-extraction`: 新增表格欄擷取；移除下一行規則；去除開頭雜訊標點。
- `excel-export`: 依表格列展開為多列輸出。
- `web-ui`: 標題模式切換、API 新增 `column_titles` 與 `rows`。

## Impact

- 程式：`ocr_engine.py`、`field_extractor.py`、`excel_writer.py`、`web.py`、`static/app.js`、`models.py`、`service.py`；新增 `table_detector.py`、`tabulate.py`。
- 瀏覽器 localStorage 標題格式由字串陣列改為物件陣列，舊資料自動轉換。
- 效能：逐格 OCR 會增加 Tesseract 呼叫次數，每頁約多數秒。
- 無新增外部相依套件。
