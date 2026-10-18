## 1. 表格偵測（TDD）

- [x] 1.1 撰寫 `table_detector.detect_cells` 失敗測試（2x3 表格、無表格、含文字儲存格）
- [x] 1.2 以 OpenCV 形態學 + connected components 實作使測試通過

## 2. OCR 引擎（TDD）

- [x] 2.1 `OcrWord` 新增 `in_table`；撰寫逐格辨識的失敗測試（儲存格字詞座標、空白格略過、表格列合併、非表格區域遮蔽後仍整頁辨識）
- [x] 2.2 實作 `TesseractOcrEngine` 逐格辨識（緊貼裁切 + 白邊 + psm 7），注入偵測器與 `image_to_string`
- [x] 2.3 預設語言改為 `chi_tra`（`config.py`、`.env.example`、測試）

## 3. 欄位擷取（TDD）

- [x] 3.1 更新測試：移除下一行規則、去除雜訊標點、標題右側空白為空字串
- [x] 3.2 撰寫 `extract_table` 失敗測試（整欄、跨頁、多欄對齊、空列與表格外文字、重複標頭、找不到）
- [x] 3.3 實作 `extract_fields` 修改與 `extract_table`

## 4. 結果展開與 Excel（TDD）

- [x] 4.1 `ExtractionResult` 新增 `rows`；`ExtractionService.extract` 接收 `column_titles`
- [x] 4.2 撰寫 `tabulate.build_table` 失敗測試（無表格欄、一筆一列、無資料列）並實作
- [x] 4.3 `excel_writer.write_workbook(header, rows)` 改為只寫檔，更新測試

## 5. API 與介面（TDD）

- [x] 5.1 更新 `/api/extract`、`/api/export` 功能測試（`column_titles`、`rows`、`table`）並實作
- [x] 5.2 前端：標題模式切換、localStorage 新格式與舊格式轉換、預覽改用 `table`

## 6. 驗證

- [x] 6.1 名冊版型測試 PDF fixture（虛構姓名）與真實 Tesseract 整合測試（Docker）
- [x] 6.2 E2E：設定 `姓名` 為表格欄、擷取名冊、預覽與 Excel 一筆一列
- [x] 6.3 Docker 全部測試與 E2E 通過

## 7. 文件

- [x] 7.1 更新 README（表格欄模式、語言預設、行為變更、版本紀錄）並提交推送
