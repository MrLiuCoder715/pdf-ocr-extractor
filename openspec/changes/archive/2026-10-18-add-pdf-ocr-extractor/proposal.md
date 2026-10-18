## Why

工程文件（例如施工圖、送審表單）多為掃描或影像型 PDF，使用者需要人工逐份翻閱並抄寫「工程編號」等欄位到 Excel，耗時且易出錯。本變更建立一套以 OpenCV + Tesseract 為核心的 PDF 文字辨識系統，讓使用者自訂要擷取的「標題」，系統自動找出標題位置並擷取其後續文字，最後彙整為 Excel。

## What Changes

- 新增 Python 專案 `pdf-ocr-extractor`（uv 管理、`src/` 版面配置）。
- 新增 PDF → 影像轉換（PyMuPDF 渲染頁面）與 OpenCV 影像前處理（灰階、去雜訊、二值化）。
- 新增 Tesseract OCR 引擎封裝，輸出含座標的「文字行」資料（繁中 + 英文）。
- 新增「標題後續文字」擷取邏輯：例如標題 `工程編號`、文字 `工程編號：nglc5zxxxd` → 值 `nglc5zxxxd`；同行無值時取下一行。
- 新增圖形介面（瀏覽器網頁介面）：匯入一或多個 PDF、自由新增／刪除擷取標題、預覽結果、下載 Excel。
- 新增 Excel 輸出：每份 PDF 一列，欄位為「檔名 + 各標題」。
- 新增 Docker 映像檔（內含 Tesseract 與繁中語言包）、`.env.example`、README、`.gitignore`。

## Capabilities

### New Capabilities
- `pdf-ocr`: 將 PDF 每頁渲染為影像，經 OpenCV 前處理後交由 Tesseract 辨識，產出帶座標的文字行。
- `field-extraction`: 依使用者提供的標題清單，在 OCR 文字行中定位標題並擷取其後續文字。
- `excel-export`: 將多份 PDF 的擷取結果輸出為 `.xlsx` 檔。
- `web-ui`: 瀏覽器圖形介面，提供 PDF 匯入、標題自由新增／刪除、結果預覽與 Excel 下載。

### Modified Capabilities
（無，此為新專案）

## Impact

- **新增相依套件**：`pymupdf`、`opencv-python-headless`、`numpy`、`pytesseract`、`openpyxl`、`flask`、`gunicorn`；開發用 `pytest`、`pytest-playwright`。
- **系統相依**：Tesseract OCR 5.x 與 `chi_tra` 語言包，透過 Docker 映像檔提供，不在本機作業系統安裝。
- **部署**：以 Docker 容器提供服務（預設 `http://localhost:8000`）。
- **版本控制**：建立 GitHub 公開儲存庫 `pdf-ocr-extractor`。
