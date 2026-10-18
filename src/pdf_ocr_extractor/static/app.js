(() => {
  const STORAGE_KEY = "pdf-ocr-extractor.titles";
  const DEFAULT_TITLES = [{ name: "工程編號", column: false }];
  const $ = (id) => document.getElementById(id);
  let lastResult = null;

  function loadTitles() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (Array.isArray(saved)) {
        // Older versions stored plain strings; treat those as field-mode titles.
        return saved
          .map((t) => (typeof t === "string" ? { name: t, column: false } : t))
          .filter((t) => t && typeof t.name === "string")
          .map((t) => ({ name: t.name, column: Boolean(t.column) }));
      }
    } catch (_) { /* storage unavailable or corrupt */ }
    return DEFAULT_TITLES.map((t) => ({ ...t }));
  }

  let titles = loadTitles();

  function saveTitles() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(titles)); } catch (_) { /* ignore */ }
  }

  function showMessage(text, isError = false) {
    $("message").textContent = text;
    $("message").classList.toggle("error", isError);
  }

  function renderTitles() {
    const list = $("title-list");
    list.replaceChildren(...titles.map((title) => {
      const li = document.createElement("li");
      const span = document.createElement("span");
      span.textContent = title.name;
      const mode = document.createElement("button");
      mode.type = "button";
      mode.className = "mode";
      mode.textContent = title.column ? "表格欄" : "欄位";
      mode.title = title.column ? "擷取標頭下方整欄資料（一筆一列）" : "擷取標題右側同一行的值";
      mode.setAttribute("aria-pressed", String(title.column));
      mode.setAttribute("aria-label", `切換 ${title.name} 模式`);
      mode.addEventListener("click", () => {
        title.column = !title.column;
        saveTitles();
        renderTitles();
      });
      const del = document.createElement("button");
      del.type = "button";
      del.textContent = "✕";
      del.setAttribute("aria-label", `刪除 ${title.name}`);
      del.addEventListener("click", () => {
        titles = titles.filter((t) => t !== title);
        saveTitles();
        renderTitles();
      });
      li.append(span, mode, del);
      return li;
    }));
  }

  $("title-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const value = $("title-input").value.trim();
    if (!value) return showMessage("標題不可為空白", true);
    if (titles.some((t) => t.name === value)) return showMessage(`「${value}」已存在`, true);
    titles.push({ name: value, column: false });
    saveTitles();
    renderTitles();
    $("title-input").value = "";
    showMessage("");
  });

  function renderResult(data) {
    const table = $("result-table");
    const head = document.createElement("tr");
    data.table.header.forEach((text) => {
      const th = document.createElement("th");
      th.textContent = text;
      head.append(th);
    });
    const rows = data.table.rows.map((cells) => {
      const tr = document.createElement("tr");
      cells.forEach((text) => {
        const td = document.createElement("td");
        td.textContent = text;
        tr.append(td);
      });
      return tr;
    });
    table.replaceChildren(head, ...rows);
    $("result-section").hidden = false;
  }

  $("extract-btn").addEventListener("click", async () => {
    const files = $("pdf-input").files;
    if (!files.length) return showMessage("請先選擇 PDF 檔案", true);
    if (!titles.length) return showMessage("請至少新增一個擷取標題", true);
    const form = new FormData();
    titles.forEach((t) => {
      form.append("titles", t.name);
      if (t.column) form.append("column_titles", t.name);
    });
    [...files].forEach((f) => form.append("files", f));
    $("extract-btn").disabled = true;
    showMessage("辨識中，請稍候…");
    try {
      const resp = await fetch("/api/extract", { method: "POST", body: form });
      const data = await resp.json();
      if (!resp.ok) return showMessage(data.error || "擷取失敗", true);
      lastResult = data;
      renderResult(data);
      showMessage(`完成，共 ${data.results.length} 份 PDF、${data.table.rows.length} 列`);
    } catch (_) {
      showMessage("無法連線到伺服器", true);
    } finally {
      $("extract-btn").disabled = false;
    }
  });

  $("download-btn").addEventListener("click", async () => {
    if (!lastResult) return;
    const resp = await fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        titles: lastResult.titles,
        column_titles: lastResult.column_titles,
        results: lastResult.results,
      }),
    });
    if (!resp.ok) return showMessage("Excel 產生失敗", true);
    const url = URL.createObjectURL(await resp.blob());
    const a = document.createElement("a");
    a.href = url;
    a.download = "ocr_results.xlsx";
    document.body.append(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  renderTitles();
})();
