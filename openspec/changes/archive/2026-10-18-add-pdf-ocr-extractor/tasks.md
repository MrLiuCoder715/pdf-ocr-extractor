## 1. 專案初始化

- [x] 1.1 以 uv 建立專案（`src/pdf_ocr_extractor`、`tests/`）、設定 `.python-version` 與 `pyproject.toml`
- [x] 1.2 查詢並確認 PyMuPDF、OpenCV、pytesseract、openpyxl、Flask、Playwright 最新用法
- [x] 1.3 加入相依套件（runtime 與 dev group）並產生 `uv.lock`
- [x] 1.4 建立 `.gitignore`、`.env.example`、`config.py`（從環境變數讀取 `OCR_LANG`、`OCR_DPI`、`MAX_PAGES`、`MAX_UPLOAD_MB`、`TESSERACT_CMD`、`PORT`）

## 2. 欄位擷取（TDD）

- [x] 2.1 撰寫 `OcrWord`/`OcrLine` 資料模型與 `field_extractor` 的失敗測試（同行、空白插入、黏字、組字規則、下一行、多標題、找不到）
- [x] 2.2 實作 `models.py` 與 `field_extractor.extract_fields` 使測試通過

## 3. PDF OCR（TDD）

- [x] 3.1 撰寫 `PyMuPdfRenderer` 失敗測試（多頁、頁數上限、無效 PDF）並實作
- [x] 3.2 撰寫 `OpenCvPreprocessor` 失敗測試（單通道、二值、尺寸不變）並實作
- [x] 3.3 撰寫 Tesseract `image_to_data` 結果聚合為 `OcrLine` 的失敗測試（假資料）並實作 `TesseractOcrEngine`
- [x] 3.4 撰寫需真實 Tesseract 的整合測試（標記 `tesseract`，無 Tesseract 時略過）

## 4. 擷取服務與 Excel 輸出（TDD）

- [x] 4.1 撰寫 `ExtractionService` 失敗測試（注入假 renderer/OCR）並實作
- [x] 4.2 撰寫 `excel_writer.write_workbook` 失敗測試（標頭、列資料、粗體凍結、文字型態）並實作

## 5. 網頁介面與 API（TDD）

- [x] 5.1 撰寫 `/api/extract` 功能測試（驗證錯誤 400、413、成功 200）並實作 Flask `create_app`
- [x] 5.2 撰寫 `/api/export` 功能測試並實作
- [x] 5.3 實作單頁介面（標題增刪、localStorage、上傳、預覽表格、下載 Excel）

## 6. 容器化

- [x] 6.1 撰寫多階段 `Dockerfile`（base 含 tesseract-ocr + chi-tra、test、runtime/gunicorn）與 `compose.yaml`
- [x] 6.2 在 Docker test 階段執行全部測試（含 Tesseract 整合測試）並通過

## 7. E2E 測試

- [x] 7.1 撰寫 Playwright E2E（新增/刪除標題、重新整理保留、上傳 PDF、預覽值、下載 Excel 驗證內容）
- [x] 7.2 以 `docker compose up` 啟動服務並在主機執行 E2E 通過

## 8. 文件與版本控制

- [x] 8.1 撰寫 README（名稱、描述、使用方式、部署步驟、授權、目錄結構、環境變數、commit 紀錄）與 LICENSE
- [x] 8.2 初始化 git、提交，並建立 GitHub 公開儲存庫 `pdf-ocr-extractor` 推送
