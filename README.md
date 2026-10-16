# pdf-ocr-extractor

以 **OpenCV + Tesseract** 辨識 PDF（含掃描檔）文字的工具。使用者在網頁介面自訂要擷取的「標題」（例如 `工程編號`），系統會找出標題位置、擷取標題後續的文字（例如 `nglc5zxxxd`），並將多份 PDF 的結果彙整為 Excel。

## 功能

- 瀏覽器圖形介面：匯入一或多個 PDF。
- 擷取標題可自由新增與刪除，清單保存在瀏覽器中（預設 `工程編號`）。
- 擷取規則：
  - 同一行：`工程編號：nglc5zxxxd` 的值為 `nglc5zxxxd`。
  - 標題下一行：標題所在行沒有值時，取同一頁的下一行。
  - 同一行有多組「標題：值」時，值擷取到下一個標題前為止。
  - 比對時忽略 OCR 插入的空白，例如 `工 程 編 號`。
- 結果預覽後可下載 Excel：每份 PDF 一列，欄位為「檔名 + 各標題」，值以文字型態保存。

## 處理流程

```
PDF ─► PyMuPDF 渲染 (300 DPI) ─► OpenCV 前處理 (灰階/去雜訊/Otsu 二值化)
    ─► Tesseract (chi_tra+eng) ─► 合併為視覺文字列 ─► 依標題擷取值 ─► openpyxl 輸出 Excel
```

## 使用方式

### 1. 啟動服務（Docker，建議）

不需在本機安裝 Tesseract，映像檔已內含 Tesseract 與繁體中文語言包。

```bash
cp .env.example .env        # 可選，調整設定
docker compose up -d --build
```

開啟瀏覽器前往 <http://localhost:8000>：

1. 在「擷取標題」輸入標題後按「新增」，按標題旁的 ✕ 可刪除。
2. 在「匯入 PDF」選擇一或多個 PDF，按「開始擷取」。
3. 確認預覽表格後，按「下載 Excel」取得 `ocr_results.xlsx`。

停止服務：`docker compose down`

### 2. 本機開發模式（需自行安裝 Tesseract）

```bash
uv sync
uv run python -m pdf_ocr_extractor   # http://127.0.0.1:8000
```

## 測試

| 層級 | 內容 | 指令 |
| --- | --- | --- |
| 單元測試 | 欄位擷取、前處理、OCR 結果聚合、Excel、設定 | `uv run pytest tests/unit` |
| 功能測試 | Flask API（注入假 OCR）、真實 Tesseract 整合 | `uv run pytest tests/functional` |
| 完整測試（含 Tesseract） | 在 Docker 中執行全部單元與功能測試 | `docker build --target test -t pdf-ocr-extractor:test . && docker run --rm pdf-ocr-extractor:test` |
| E2E | Playwright 驅動瀏覽器：標題增刪、上傳、擷取、下載 Excel | 見下方 |

需要真實 Tesseract 的測試標記為 `tesseract`，本機沒有 Tesseract 時會自動略過，在 Docker 中則會執行。

E2E 測試：

```bash
docker compose up -d --build
uv run playwright install chromium
uv run pytest -m e2e            # 可用 E2E_BASE_URL 指定其他網址
```

## 部署步驟

1. 安裝 Docker（含 Docker Compose）。
2. `git clone https://github.com/MrLiuCoder715/pdf-ocr-extractor.git && cd pdf-ocr-extractor`
3. `cp .env.example .env`，依需求調整設定。
4. `docker compose up -d --build`
5. 前往 `http://localhost:<PORT>`。

> 服務預設只綁定 `127.0.0.1`，供本機單人使用，本身沒有登入機制。若要對外開放給多人使用，必須先加上 OAuth 驗證。

## 環境變數

| 變數 | 預設值 | 說明 |
| --- | --- | --- |
| `OCR_LANG` | `chi_tra+eng` | Tesseract 語言 |
| `OCR_DPI` | `300` | PDF 渲染解析度；提高可改善辨識，但會變慢 |
| `MAX_PAGES` | `20` | 每份 PDF 最多處理的頁數 |
| `MAX_UPLOAD_MB` | `50` | 單次上傳總大小上限（MB），超過時回傳 413 |
| `TESSERACT_CMD` | （空） | Tesseract 執行檔路徑，留空則使用 PATH |
| `PORT` | `8000` | 服務埠號 |

## 目錄結構

```
pdf-ocr-extractor/
├── src/pdf_ocr_extractor/
│   ├── config.py           # 環境變數設定
│   ├── models.py           # OcrWord / OcrLine / ExtractionResult
│   ├── pdf_renderer.py     # PyMuPDF：PDF → 影像
│   ├── preprocess.py       # OpenCV 前處理
│   ├── ocr_engine.py       # Tesseract 辨識與視覺列合併
│   ├── field_extractor.py  # 依標題擷取後續文字
│   ├── service.py          # 串接整個處理流程
│   ├── excel_writer.py     # openpyxl 輸出
│   ├── web.py              # Flask 介面與 API
│   ├── templates/index.html
│   └── static/             # app.js、style.css
├── tests/
│   ├── unit/               # 單元測試
│   ├── functional/         # API 功能測試、Tesseract 整合測試
│   └── e2e/                # Playwright 瀏覽器測試
├── openspec/               # OpenSpec 規格（proposal / design / specs / tasks）
├── Dockerfile              # base / test / runtime 多階段建置
├── compose.yaml
├── .env.example
└── pyproject.toml
```

## API

| 方法 | 路徑 | 說明 |
| --- | --- | --- |
| `GET` | `/` | 網頁介面 |
| `POST` | `/api/extract` | multipart 欄位 `files`（可多個）、`titles`（可多個），回傳 `{titles, results:[{filename, fields}]}` |
| `POST` | `/api/export` | JSON `{titles, results}`，回傳 `.xlsx` |

## 已知限制

- OCR 可能把相似字元辨識錯誤（例如 `0`/`O`、`l`/`1`），下載前請先在預覽表格中確認。
- 標題本身若被辨識錯誤就無法比對，目前不支援模糊比對。
- 同一標題在同一份 PDF 中出現多次時，只取第一個。

## 版本紀錄（Commit Log）

| 版本 | 日期 | 說明 |
| --- | --- | --- |
| v0.1.0 | 2026-10-16 | 初始版本：OpenCV + Tesseract OCR、標題擷取、網頁介面、Excel 匯出、Docker、單元／功能／E2E 測試 |

## 授權

[MIT License](LICENSE)
