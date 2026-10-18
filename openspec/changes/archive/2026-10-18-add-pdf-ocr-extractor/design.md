## Context

- 新專案，資料夾 `pdf-ocr-extractor` 原為空。
- 指定技術：Python、OpenCV + Tesseract 進行影像與文字辨識、結果輸出 Excel。
- 開發規範：TDD、SOLID、MVP；全面 Docker 化，避免在本機作業系統安裝原生套件；E2E 測試須使用瀏覽器自動化工具；機密資訊由環境變數提供。
- 開發機（Windows 11）未安裝 Tesseract，已安裝 Docker 與 uv。

## Goals / Non-Goals

**Goals:**
- 使用者在圖形介面匯入 PDF、自由增刪標題、一鍵擷取並下載 Excel。
- 以標題為錨點擷取「標題後續文字」（同行優先，同行無值取下一行）。
- 核心邏輯與介面、OCR 引擎解耦，可在無 Tesseract 的情況下進行單元測試。

**Non-Goals:**
- 不做版面範本／座標框選設定（MVP 只用標題錨點）。
- 不做 PDF 文字層直接讀取的捷徑（一律走 OCR，符合指定技術）。
- 不做多使用者帳號系統；本工具為本機單人使用，綁定 localhost。若未來對外部署，須依規範加入 OAuth。
- 不做表格結構辨識、手寫辨識。

## Decisions

### D1. 圖形介面採用「瀏覽器網頁介面（Flask）」而非桌面視窗（tkinter）
- **理由**：Tesseract 必須存在於執行環境。網頁介面可讓應用程式、Tesseract、介面全部在 Docker 內執行，使用者只需開瀏覽器；且 E2E 測試可用 Playwright 驅動瀏覽器，符合規範。
- **替代方案**：tkinter 桌面程式 → 需在 Windows 原生安裝 Tesseract（違反 Docker 原則），且無法以瀏覽器自動化工具做 E2E；Streamlit → 開發快，但 UI 行為與測試較難細部控制，且增加大型相依。

### D2. PDF 渲染採用 PyMuPDF
- **理由**：純 Python wheel，不需 poppler；可直接取得像素陣列轉為 numpy 給 OpenCV。預設 300 DPI（可由 `OCR_DPI` 調整）。
- **替代方案**：`pdf2image` 需 poppler 系統套件，增加映像檔體積與設定成本。

### D3. OpenCV 前處理流程
灰階 → 中值濾波去雜訊 → Otsu 二值化。保持簡單；若辨識率不足再加入 deskew（列為後續改善）。

### D4. OCR 結果結構化為「文字行」
使用 `pytesseract.image_to_data`（`Output.DICT`），依 `(page, block_num, par_num, line_num)` 聚合 words 成 `OcrLine(page, words: list[OcrWord], bbox)`，`OcrWord(text, left, top, width, height, conf)`。過濾 `conf < 0` 與空字串。接著將同頁中垂直重疊 ≥ 50%（以較矮者為基準）的文字行合併為同一視覺列，以處理表格式表單中標題與值被 Tesseract 分到不同 block 的情況；列依 top 排序、字詞依 left 排序。
- 語言預設 `chi_tra+eng`（`OCR_LANG`），Tesseract 執行檔路徑可由 `TESSERACT_CMD` 覆寫。

### D5. 欄位擷取演算法（純函式，不依賴 OCR）
1. 標題與每行文字皆「移除空白」後比對（Tesseract 對中文常在字間插入空白）。
2. 在行內找到標題後，取其**之後**的 words 組成值；去除開頭分隔符（`:`、`：`、`-`、`=` 及空白）。
3. 組字規則：前一 token 以 ASCII 英數結尾且後一 token 以 ASCII 英數開頭時以空白連接，否則直接相連（避免中文與 `2026/ 10/ 16` 這類被拆開的值多出空白）。
4. 值若遇到另一個使用者設定的標題即截斷（避免同列多組「標題：值」被合併）。
5. 同行無值時，取同一頁中**下一行**的文字作為值。
6. 每份 PDF 依頁序、行序取**第一個**命中值；找不到則為空字串。
- **替代方案**：正則 `標題[:：]\s*(\S+)` 套整頁文字 → 對中文空白、跨行情況較脆弱。

### D6. 分層與依賴反轉（SOLID）
```
web (Flask routes)  ──►  ExtractionService
                          ├─ PdfRenderer        (Protocol)  → PyMuPdfRenderer
                          ├─ ImagePreprocessor  (Protocol)  → OpenCvPreprocessor
                          ├─ OcrEngine          (Protocol)  → TesseractOcrEngine
                          └─ FieldExtractor     (純函式 extract_fields)
excel_writer.write_workbook(results, titles) → bytes
```
`create_app(service=...)` 以注入方式取得 service，功能測試可注入假 OCR 引擎。

### D7. 無狀態 API
- `GET /` → 單頁介面（HTML + 原生 JS）。
- `POST /api/extract`（multipart：`files[]`、`titles[]`）→ JSON `{titles, results:[{filename, fields:{title:value}}]}`。
- `POST /api/export`（JSON：`{titles, results}`）→ `.xlsx` 下載。
- 標題清單存於瀏覽器 `localStorage`（預設 `["工程編號"]`），伺服器不保存狀態。

### D8. Excel 格式
openpyxl；工作表 `擷取結果`；第一列標頭 `檔名, <標題1>, <標題2>…`，粗體並凍結首列；每份 PDF 一列。

### D9. 容器化與測試分層
- `Dockerfile` 多階段：`base`（uv + tesseract-ocr + tesseract-ocr-chi-tra）、`test`（含 dev 相依，執行 pytest）、`runtime`（gunicorn）。
- 單元測試：field_extractor、preprocess、excel_writer、ocr 行聚合（以假資料）、輸入驗證。
- 功能測試：Flask test client + 假 OCR 引擎；另有需真實 Tesseract 的整合測試（標記 `tesseract`，於 Docker 中執行，本機無 Tesseract 時自動略過）。
- E2E：`docker compose` 啟動服務，主機以 Playwright（Chromium）操作介面：新增標題、上傳 PDF、擷取、下載 Excel 並驗證內容。

## Risks / Trade-offs

- [OCR 辨識錯字（例如 `0`/`O`、`l`/`1`）] → 提高 DPI、二值化；結果在介面預覽，使用者可確認後再下載。
- [標題本身被辨識錯誤導致找不到] → 比對前移除空白；MVP 不做模糊比對，列為後續改善。
- [大型 PDF 處理時間長] → `MAX_PAGES`、`MAX_UPLOAD_MB` 環境變數限制；gunicorn timeout 調高。
- [上傳非 PDF 或惡意檔案] → 檢查副檔名與 `%PDF-` 檔頭、限制大小、只在記憶體處理不落地。
- [網頁介面需先啟動容器] → README 提供一行 `docker compose up` 指令。

## Open Questions

- 同一份 PDF 中同一標題出現多次時，是否需要全部列出？（MVP：取第一個）
