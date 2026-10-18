# pdf-ocr-extractor

以 **OpenCV + Tesseract** 辨識 PDF（含掃描檔）文字的工具。使用者在網頁介面自訂要擷取的「標題」（例如 `工程編號`），系統會找出標題位置、擷取標題後續的文字（例如 `nglc5zxxxd`），並將多份 PDF 的結果彙整為 Excel。

## 功能

- 瀏覽器圖形介面：匯入一或多個 PDF。
- 擷取標題可自由新增與刪除，清單與模式保存在瀏覽器中（預設 `工程編號`）。
- 每個標題可切換兩種模式：

  | 模式 | 適用 | 規則 |
  | --- | --- | --- |
  | **欄位**（預設） | `工程編號：nglc5zxxxd` 這類「標籤＋值」 | 取標題右側同一行的值；同一行有多組「標題：值」時擷取到下一個標題前；右側沒有值時為空白 |
  | **表格欄** | 名冊、清單等表格中的一整欄（例如 `姓名`） | 以表格標頭為準，擷取其下方同一欄的每一列，**含沒有表頭的後續頁面** |

- 比對時忽略 OCR 插入的空白，例如表頭 `姓 名` 可用標題 `姓名` 擷取。
- **標題必須與文件上的文字相同**：例如文件寫的是「承商名稱」，標題就要設為 `承商名稱`，設成 `廠商` 會找不到。
- 有框線的表格會先由 OpenCV 偵測出每個儲存格，再逐格辨識。
- 結果預覽後可下載 Excel，值以文字型態保存：
  - 只有「欄位」時，每份 PDF 一列。
  - 有「表格欄」時，每個表格列一列，檔名與欄位值在每列重複（一筆一列）。

## 處理流程

```
PDF ─► PyMuPDF 渲染 (300 DPI) ─► OpenCV 前處理 (灰階/去雜訊/Otsu 二值化)
    ─► OpenCV 表格偵測 (形態學找框線 → 儲存格)
    ─► Tesseract (chi_tra)：儲存格逐格辨識 ＋ 表格外區域整頁辨識
    ─► 合併為視覺文字列 ─► 依標題擷取（欄位／表格欄） ─► openpyxl 輸出 Excel
```

## 使用方式

### 1. 啟動服務（Docker，建議）

不需在本機安裝 Tesseract，映像檔已內含 Tesseract 與繁體中文語言包。

```bash
cp .env.example .env        # 可選，調整設定
docker compose up -d --build
```

開啟瀏覽器前往 <http://localhost:8000>：

1. 在「擷取標題」輸入標題後按「新增」，按標題旁的 ✕ 可刪除；按「欄位／表格欄」按鈕切換模式。
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
| 單元測試 | 欄位與表格欄擷取、表格偵測、逐格 OCR、前處理、結果展開、Excel、設定 | `uv run pytest tests/unit` |
| 功能測試 | Flask API（注入假 OCR）、真實 Tesseract 整合（含名冊版型表格） | `uv run pytest tests/functional` |
| 完整測試（含 Tesseract） | 在 Docker 中執行全部單元與功能測試 | `docker build --target test -t pdf-ocr-extractor:test . && docker run --rm pdf-ocr-extractor:test` |
| E2E | Playwright 驅動瀏覽器：標題增刪、模式切換、上傳、擷取、表格欄一筆一列、下載 Excel | 見下方 |

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
| `OCR_LANG` | `chi_tra` | Tesseract 語言。`chi_tra` 已能辨識英數字；`chi_tra+eng` 會把部分中文姓名誤判為英文，不建議使用 |
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
│   ├── table_detector.py   # OpenCV 表格框線與儲存格偵測
│   ├── ocr_engine.py       # Tesseract 逐格／整頁辨識與視覺列合併
│   ├── field_extractor.py  # 欄位擷取與表格欄擷取
│   ├── tabulate.py         # 結果展開為預覽／Excel 的列
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
| `POST` | `/api/extract` | multipart 欄位 `files`、`titles`、`column_titles`（皆可多個），回傳 `{titles, column_titles, results:[{filename, fields, rows}], table:{header, rows}}` |
| `POST` | `/api/export` | JSON `{titles, column_titles, results}`，回傳 `.xlsx` |

## 已知限制

- OCR 可能把相似字元辨識錯誤（例如 `0`/`O`、`l`/`1`），下載前請先在預覽表格中確認。
- 標題本身若被辨識錯誤就無法比對，目前不支援模糊比對。
- 「欄位」模式下，同一標題在同一份 PDF 中出現多次時只取第一個。
- 「表格欄」以座標對齊同一欄；無框線的表格、單一儲存格內多行文字，準確度較低。
- 照片儲存格也會被辨識（產生雜訊字），但只要不是使用者選的表格欄就不會輸出。

## 版本紀錄（Commit Log）

| 版本 | 日期 | Commit／說明 |
| --- | --- | --- |
| v0.2.0 | 2026-10-18 | `0184fc2` 表格欄擷取模式（一筆一列）、OpenCV 表格偵測與逐格 OCR、預設語言改為 `chi_tra`、移除「取下一行」規則、去除 OCR 雜訊標點 |
| v0.1.0 | 2026-10-16 | `3006c6c` 初始版本：OpenCV + Tesseract OCR、標題擷取、網頁介面、Excel 匯出、Docker、單元／功能／E2E 測試 |

## 授權

[MIT License](LICENSE)
