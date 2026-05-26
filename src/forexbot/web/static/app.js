const state = {
  config: null,
};

const defaults = {
  mt5: {
    account_number: 12345678,
    terminal_path: null,
    server: null,
    magic: 260526,
    deviation_points: 20,
    order_comment: "forexbot-v2",
    type_filling: "RETURN",
  },
};

const form = document.querySelector("#config-form");
const messageLine = document.querySelector("#message-line");
const symbolsBody = document.querySelector("#symbols-body");

function showMessage(message, isError = false) {
  messageLine.textContent = message;
  messageLine.classList.toggle("error", isError);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed: ${response.status}`);
  }
  return payload;
}

function getPath(source, path) {
  return path.split(".").reduce((value, key) => (value == null ? undefined : value[key]), source);
}

function setInputValue(name, value) {
  const input = form.elements[name];
  if (!input) {
    return;
  }
  input.value = value == null ? "" : value;
}

function fillForm(config) {
  for (const element of form.elements) {
    if (!element.name || element.closest("#symbols-body")) {
      continue;
    }
    setInputValue(element.name, getPath(config, element.name));
  }
  renderSymbols(config.symbols || []);
}

function inputNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function nullableString(value) {
  const trimmed = String(value || "").trim();
  return trimmed === "" ? null : trimmed;
}

function readConfig() {
  const mt5 = {
    account_number: inputNumber(form.elements["mt5.account_number"].value, defaults.mt5.account_number),
    terminal_path: nullableString(form.elements["mt5.terminal_path"].value),
    server: nullableString(form.elements["mt5.server"].value),
    magic: inputNumber(form.elements["mt5.magic"].value, defaults.mt5.magic),
    deviation_points: inputNumber(form.elements["mt5.deviation_points"].value, defaults.mt5.deviation_points),
    order_comment: form.elements["mt5.order_comment"].value.trim() || defaults.mt5.order_comment,
    type_filling: form.elements["mt5.type_filling"].value || defaults.mt5.type_filling,
  };

  const config = {
    mode: form.elements.mode.value,
    account: {
      starting_equity: inputNumber(form.elements["account.starting_equity"].value),
    },
    risk: {
      risk_per_trade_pct: inputNumber(form.elements["risk.risk_per_trade_pct"].value),
      max_daily_loss_pct: inputNumber(form.elements["risk.max_daily_loss_pct"].value),
      max_open_trades: inputNumber(form.elements["risk.max_open_trades"].value),
      max_open_trades_per_symbol: inputNumber(form.elements["risk.max_open_trades_per_symbol"].value),
    },
    strategy: {
      fast_sma: inputNumber(form.elements["strategy.fast_sma"].value),
      slow_sma: inputNumber(form.elements["strategy.slow_sma"].value),
      atr_period: inputNumber(form.elements["strategy.atr_period"].value),
      atr_stop_multiplier: inputNumber(form.elements["strategy.atr_stop_multiplier"].value),
      take_profit_r_multiple: inputNumber(form.elements["strategy.take_profit_r_multiple"].value),
      max_spread_points: inputNumber(form.elements["strategy.max_spread_points"].value),
    },
    market_data: {
      provider: form.elements["market_data.provider"].value.trim(),
      path: form.elements["market_data.path"].value.trim(),
    },
    symbols: readSymbols(),
  };

  if (config.mode === "mt5_demo" || config.mode === "mt5_live" || state.config?.mt5) {
    config.mt5 = mt5;
  }
  return config;
}

function renderSymbols(symbols) {
  symbolsBody.textContent = "";
  for (const symbol of symbols) {
    symbolsBody.appendChild(createSymbolRow(symbol));
  }
}

function createSymbolRow(symbol = {}) {
  const row = document.createElement("div");
  row.className = "symbol-row";
  row.innerHTML = `
    <input data-key="name" type="text" value="${escapeAttr(symbol.name || "")}" aria-label="Symbol name">
    <input data-key="point" type="number" min="0" step="0.00001" value="${escapeAttr(symbol.point || "")}" aria-label="Point">
    <input data-key="point_value_per_lot" type="number" min="0" step="0.01" value="${escapeAttr(symbol.point_value_per_lot || "")}" aria-label="Point value per lot">
    <input data-key="min_volume" type="number" min="0" step="0.01" value="${escapeAttr(symbol.min_volume || "")}" aria-label="Minimum volume">
    <input data-key="max_volume" type="number" min="0" step="0.01" value="${escapeAttr(symbol.max_volume || "")}" aria-label="Maximum volume">
    <input data-key="volume_step" type="number" min="0" step="0.01" value="${escapeAttr(symbol.volume_step || "")}" aria-label="Volume step">
    <button type="button" data-remove-symbol>Remove</button>
  `;
  row.querySelector("[data-remove-symbol]").addEventListener("click", () => row.remove());
  return row;
}

function readSymbols() {
  return [...symbolsBody.querySelectorAll(".symbol-row")].map((row) => ({
    name: row.querySelector('[data-key="name"]').value.trim().toUpperCase(),
    point: inputNumber(row.querySelector('[data-key="point"]').value),
    point_value_per_lot: inputNumber(row.querySelector('[data-key="point_value_per_lot"]').value),
    min_volume: inputNumber(row.querySelector('[data-key="min_volume"]').value),
    max_volume: inputNumber(row.querySelector('[data-key="max_volume"]').value),
    volume_step: inputNumber(row.querySelector('[data-key="volume_step"]').value),
  }));
}

function escapeAttr(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function setBusy(isBusy) {
  for (const button of document.querySelectorAll("button")) {
    button.disabled = isBusy;
  }
}

async function refreshStatus() {
  const status = await requestJson("/api/status");
  document.querySelector("#status-mode").textContent = status.mode || "--";
  document.querySelector("#status-host").textContent = status.host || "--";
  document.querySelector("#status-summary").textContent = status.last_summary || "No cycle run yet";
}

async function refreshJournal() {
  const journal = await requestJson("/api/journal");
  document.querySelector("#journal-entries").textContent = journal.entries.length
    ? journal.entries.join("\n")
    : "No journal entries";
}

async function loadDashboard() {
  try {
    const [config] = await Promise.all([requestJson("/api/config"), refreshStatus(), refreshJournal()]);
    state.config = config;
    fillForm({ mt5: defaults.mt5, ...config });
    showMessage("Ready");
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function runAction(label, action) {
  setBusy(true);
  showMessage(`${label}...`);
  try {
    const result = await action();
    await Promise.all([refreshStatus(), refreshJournal()]);
    showMessage(result.summary || result.ok ? `${label} complete` : label);
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  runAction("Save Config", async () => {
    const config = readConfig();
    const result = await requestJson("/api/config", {
      method: "POST",
      body: JSON.stringify(config),
    });
    state.config = config;
    return result;
  });
});

document.querySelector("#check-config").addEventListener("click", () => {
  runAction("Check Config", () => requestJson("/api/check-config", { method: "POST" }));
});

document.querySelector("#run-once").addEventListener("click", () => {
  runAction("Run One Cycle", () => requestJson("/api/run-once", { method: "POST" }));
});

document.querySelector("#backtest").addEventListener("click", () => {
  runAction("Backtest", () => requestJson("/api/backtest", { method: "POST" }));
});

document.querySelector("#refresh-journal").addEventListener("click", () => {
  runAction("Refresh Journal", refreshJournal);
});

document.querySelector("#add-symbol").addEventListener("click", () => {
  symbolsBody.appendChild(createSymbolRow());
});

loadDashboard();
