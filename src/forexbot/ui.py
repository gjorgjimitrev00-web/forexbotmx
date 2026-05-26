from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from forexbot.config import ConfigError, load_config
from forexbot.runtime import build_engine_from_config


def create_app(
    *,
    config_path: Path = Path("configs/paper.yaml"),
    journal_path: Path = Path("journals/ui.jsonl"),
) -> FastAPI:
    app = FastAPI(title="Forexbot Control Panel")
    app.state.config_path = config_path
    app.state.journal_path = journal_path
    app.state.last_summary = None

    @app.get("/", response_class=HTMLResponse)
    def dashboard() -> str:
        return "<!doctype html><html><body><h1>Forexbot</h1><div id='app'></div></body></html>"

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        config = load_config(app.state.config_path)
        return {"host": "127.0.0.1", "mode": config.mode, "last_summary": app.state.last_summary}

    @app.get("/api/config")
    def get_config() -> dict[str, Any]:
        return yaml.safe_load(app.state.config_path.read_text(encoding="utf-8"))

    @app.post("/api/config")
    def save_config(payload: dict[str, Any]) -> dict[str, Any]:
        config_text = yaml.safe_dump(payload, sort_keys=False)
        config_path = app.state.config_path
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w",
            delete=False,
            dir=config_path.parent,
            encoding="utf-8",
            suffix=".tmp",
        ) as temp_file:
            temp_file.write(config_text)
            temp_path = Path(temp_file.name)
        try:
            load_config(temp_path)
        except ConfigError as exc:
            temp_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        temp_path.replace(config_path)
        return {"ok": True}

    @app.post("/api/check-config")
    def check_config() -> dict[str, Any]:
        try:
            config = load_config(app.state.config_path)
        except (ConfigError, OSError, KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"ok": True, "mode": config.mode, "symbols": len(config.symbols)}

    @app.post("/api/run-once")
    def run_once() -> dict[str, Any]:
        config = load_config(app.state.config_path)
        if config.mode == "backtest":
            raise HTTPException(status_code=400, detail="run-once does not accept backtest mode")
        summary = build_engine_from_config(config, app.state.journal_path).run_once()
        app.state.last_summary = summary
        return {"summary": summary}

    @app.post("/api/backtest")
    def backtest() -> dict[str, Any]:
        config = load_config(app.state.config_path)
        if config.mode != "backtest":
            raise HTTPException(status_code=400, detail="backtest endpoint requires backtest mode")
        summary = build_engine_from_config(config, app.state.journal_path).run_once()
        app.state.last_summary = summary
        return {"summary": summary}

    @app.get("/api/journal")
    def journal() -> dict[str, Any]:
        if not app.state.journal_path.exists():
            return {"entries": []}
        lines = app.state.journal_path.read_text(encoding="utf-8").splitlines()[-100:]
        return {"entries": lines}

    return app
