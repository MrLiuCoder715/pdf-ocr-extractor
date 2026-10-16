(() => {
  const STORAGE_KEY = "pdf-ocr-extractor.titles";
  const DEFAULT_TITLES = ["工程編號"];
  const $ = (id) => document.getElementById(id);
  let lastResult = null;

  function loadTitles() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      if (Array.isArray(saved)) return saved.filter((t) => typeof t === "string");
    } catch (_) { /* storage unavailable or corrupt */ }
    return [...DEFAULT_TITLES];
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
      span.textContent = title;
      const del = document.createElement("button");
      del.type = "button";
      del.textContent = "✕";
      del.setAttribute("aria-label", `刪除 ${title}`);
      del.addEventListener("click", () => {
        titles = titles.filter((t) => t !== title);
        saveTitles();
        renderTitles();
      });
      li.append(span, del);
      return li;
    }));
  }

  $("title-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const value = $("title-input").value.trim();
    if (!value) return showMessage("標題不可為空白", true);
    if (titles.includes(value)) return showMessage(`「${value}」已存在`, true);
    titles.push(value);
    saveTitles();
    renderTitles();
    $("title-input").value = "";
    showMessage("");
  });

  function renderResult(data) {
    const table = $("result-table");
    const head = document.createElement("tr");
    ["檔名", ...data.titles].forEach((text) => {
      const th = document.createElement("th");
      th.textContent = text;
      head.append(th);
    });
    const rows = data.results.map((r) => {
      const tr = document.createElement("tr");
      [r.filename, ...data.titles.map((t) => r.fields[t] ?? "")].forEach((text) => {
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
    titles.forEach((t) => form.append("titles", t));
    [...files].forEach((f) => form.append("files", f));
    $("extract-btn").disabled = true;
    showMessage("辨識中，請稍候…");
    try {
      const resp = await fetch("/api/extract", { method: "POST", body: form });
      const data = await resp.json();
      if (!resp.ok) return showMessage(data.error || "擷取失敗", true);
      lastResult = data;
      renderResult(data);
      showMessage(`完成，共 ${data.results.length} 份 PDF`);
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
      body: JSON.stringify(lastResult),
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
