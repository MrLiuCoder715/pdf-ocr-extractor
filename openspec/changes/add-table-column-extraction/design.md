## Context

以名冊版型（頁首「承商名稱／工程編號／契約編號／契約名稱」標籤，下方為「項次｜姓 名｜大頭照」框線表格，表格跨 3 頁且後續頁沒有標頭）重建測試 PDF，在 Docker 中以真實 Tesseract 實驗：

| 策略 | 結果 |
| --- | --- |
| 現行（psm 3，整頁） | 只辨識出頁首標籤，表格與第 2、3 頁全空 |
| psm 11 | 表格內幾乎只得到雜訊 |
| 移除框線 + psm 3 | 部分姓名出現，`林志玲`、`趙六安` 遺失 |
| **逐格裁切（緊貼文字）+ psm 7 + `chi_tra`** | **全部姓名、項次正確** |
| 同上但 `chi_tra+eng` | `林志玲`→`MEK`、`趙六安`→`MAR` |

## Goals / Non-Goals

**Goals:**
- 正確辨識框線表格的每個儲存格，並保留儲存格座標。
- 依欄位標頭擷取整欄資料（跨頁），一筆一列輸出。
- 修正空值誤抓下一行的問題。

**Non-Goals:**
- 無框線表格的欄位切分（仍以文字座標近似處理，不保證準確）。
- 單一儲存格內多行文字（MVP 以單行模式辨識）。
- 讀取 PDF 文字層（維持 OCR 路線）。

## Decisions

### D1. 表格偵測（`table_detector.py`，OpenCV）
1. 二值影像反相後，以長條形結構元素（水平 `(k,1)`、垂直 `(1,k)`，`k = max(40, min(H,W)//40)`）做 morphological open，取得框線遮罩；字的筆畫長度遠小於 `k`，不會被當成框線。
2. 對「非框線區域」做 connected components：每個儲存格內部是一個獨立連通區；表格外背景會碰到影像邊緣，予以排除。再排除過小的區域（寬或高 < 15px）。
- **替代方案**：`findContours` + 階層過濾 → 需處理外框與巢狀輪廓，較繁瑣。

### D2. 辨識流程（`TesseractOcrEngine`）
- **儲存格**：裁切內部 → 依墨點範圍緊貼裁切並加白邊 → `image_to_string(psm 7)`。空白儲存格不產生字詞。產生的 `OcrWord` 座標為**儲存格框**，並標記 `in_table=True`。
- **非表格區域**：把框線與儲存格塗白後做整頁 `image_to_data`（與既有流程相同）。
- 兩者合併後沿用既有「垂直重疊合併為視覺列」邏輯；同一表格列的儲存格高度、位置相同，會自然合併為同一列。
- `image_to_string`、`image_to_data` 與偵測器皆以建構子注入，單元測試不需 Tesseract。

### D3. 預設語言 `chi_tra`
實驗顯示 `chi_tra` 對 `21915A451`、`MSER` 等英數字的辨識結果與 `chi_tra+eng` 相同，但不會把中文姓名誤判為英文。仍可由 `OCR_LANG` 覆寫。

### D4. 表格欄擷取（`extract_table`）
1. 找出第一個含標題的文字行與字詞範圍，取得欄位水平範圍 `[x0, x1]`。
2. 對標頭之後的所有文字行（含後續頁面）：取水平重疊 ≥ 50%（以較窄者為基準）的字詞組成該欄值；若標頭位於表格內，只採用 `in_table` 的字詞，避免頁尾等文字混入。
3. 多個表格欄依「同一文字行」對齊為一列；所有表格欄皆為空的列略過；再次出現的標頭列（如每頁重複表頭）略過。
- **替代方案**：依儲存格網格（row/col index）建模 → 需跨頁對齊網格，複雜度高；以座標重疊即可涵蓋同版型的續頁。

### D5. 移除「下一行」規則
它在「標題存在但值為空白」時會抓到下一行的其他標籤，結果錯誤且難以察覺。值位於標題下方的情況改由「表格欄」模式處理。

### D6. 輸出展開集中於 `tabulate.build_table`
`build_table(results, titles, column_titles) -> (header, rows)` 為唯一的展開邏輯，同時供 `/api/extract` 預覽與 Excel 輸出使用，確保兩者一致。`excel_writer.write_workbook(header, rows)` 只負責寫檔。

### D7. API 與前端
- `POST /api/extract` 新增可重複的 `column_titles`（須為 `titles` 的子集）。回應：`{titles, column_titles, results:[{filename, fields, rows}], table:{header, rows}}`。
- `POST /api/export` 接收 `{titles, column_titles, results}`。
- localStorage 改存 `[{name, column}]`；讀到舊的字串陣列時轉為 `column:false`。

## Risks / Trade-offs

- [逐格 OCR 較慢] → 每格一次 Tesseract 呼叫，名冊每頁約十餘格，可接受；`MAX_PAGES` 仍有效。
- [照片儲存格產生雜訊字] → 只影響「大頭照」欄；不屬於使用者選的表格欄時不會輸出。
- [無框線表格] → 退回座標重疊判斷，準確度較低，列為已知限制。
- [移除下一行規則為行為變更] → README 與介面說明「值在下方請用表格欄」。
