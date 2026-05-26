import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

import forexbot.cli as cli


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA_PATH = PROJECT_ROOT / "data" / "sample_candles.json"


def _subprocess_env() -> dict[str, str]:
    src_path = PROJECT_ROOT / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        path for path in (str(src_path), env.get("PYTHONPATH", "")) if path
    )
    return env


def _write_temp_config(
    tmp_path: Path,
    config_name: str,
    market_data_path: Path = SAMPLE_DATA_PATH,
) -> Path:
    source = PROJECT_ROOT / "configs" / config_name
    config_text = source.read_text(encoding="utf-8").replace(
        "path: data/sample_candles.json",
        f"path: {market_data_path}",
    )
    target = tmp_path / config_name
    target.write_text(config_text, encoding="utf-8")
    return target


def _write_temp_config_with_mode(tmp_path: Path, config_name: str, mode: str) -> Path:
    config_path = _write_temp_config(tmp_path, config_name)
    config_text = config_path.read_text(encoding="utf-8")
    source_mode = config_name.removesuffix(".yaml")
    config_path.write_text(
        config_text.replace(f"mode: {source_mode}", f"mode: {mode}"),
        encoding="utf-8",
    )
    return config_path


def _run_cli(args: list[str], tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "forexbot", *args],
        check=False,
        capture_output=True,
        cwd=tmp_path,
        env=_subprocess_env(),
        text=True,
    )


def test_check_config_command_succeeds(tmp_path):
    config_path = _write_temp_config(tmp_path, "paper.yaml")

    result = _run_cli(["check-config", "--config", str(config_path)], tmp_path)

    assert result.returncode == 0
    assert "mode=paper" in result.stdout


def test_run_once_command_succeeds(tmp_path):
    config_path = _write_temp_config(tmp_path, "paper.yaml")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode == 0
    assert "executed" in result.stdout
    assert (tmp_path / "journals" / "paper.jsonl").exists()


def test_run_accepts_mt5_demo_mode_without_v1_rejection(tmp_path):
    config_path = _write_temp_config(tmp_path, "mt5_demo.yaml")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "runtime error:" in result.stdout
    assert "MT5 demo execution is disabled in V1" not in result.stdout
    assert "run requires mode=paper" not in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_run_accepts_mt5_live_mode_without_v1_rejection(tmp_path):
    config_path = _write_temp_config_with_mode(tmp_path, "mt5_demo.yaml", "mt5_live")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "runtime error:" in result.stdout
    assert "MT5 demo execution is disabled in V1" not in result.stdout
    assert "run requires mode=paper" not in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("mode", ["mt5_demo", "mt5_live"])
def test_run_uses_mode_specific_summary_and_journal_for_mt5_modes(tmp_path, monkeypatch, capsys, mode):
    config_path = _write_temp_config_with_mode(tmp_path, "mt5_demo.yaml", mode)
    captured = {}

    class FakeEngine:
        def run_once(self):
            return {"executed": 0, "blocked": 0, "held": 0, "duplicates": 0, "errors": 0}

    def fake_build_engine_from_config(config, journal_path):
        captured["mode"] = config.mode
        captured["journal_path"] = journal_path
        return FakeEngine()

    monkeypatch.setattr(cli, "build_engine_from_config", fake_build_engine_from_config)

    result = cli.main(["run", "--config", str(config_path), "--once"])

    assert result == 0
    assert captured == {"mode": mode, "journal_path": f"journals/{mode}.jsonl"}
    assert f"{mode} summary:" in capsys.readouterr().out


def test_run_rejects_backtest_mode_without_traceback(tmp_path):
    config_path = _write_temp_config(tmp_path, "backtest.yaml")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "run requires mode=paper, mt5_demo, or mt5_live" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_backtest_command_succeeds(tmp_path):
    config_path = _write_temp_config(tmp_path, "backtest.yaml")

    result = _run_cli(["backtest", "--config", str(config_path)], tmp_path)

    assert result.returncode == 0
    assert "backtest summary" in result.stdout
    assert (tmp_path / "journals" / "backtest.jsonl").exists()


def test_backtest_rejects_mt5_demo_mode_without_traceback(tmp_path):
    config_path = _write_temp_config(tmp_path, "mt5_demo.yaml")

    result = _run_cli(["backtest", "--config", str(config_path)], tmp_path)

    assert result.returncode != 0
    assert "backtest requires mode=backtest; got mode=mt5_demo" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_backtest_rejects_paper_mode_without_traceback(tmp_path):
    config_path = _write_temp_config(tmp_path, "paper.yaml")

    result = _run_cli(["backtest", "--config", str(config_path)], tmp_path)

    assert result.returncode != 0
    assert "backtest requires mode=backtest" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_run_reports_runtime_error_for_missing_market_data(tmp_path):
    config_path = _write_temp_config(tmp_path, "paper.yaml", tmp_path / "missing.json")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "runtime error:" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_run_fails_when_engine_summary_has_symbol_errors(tmp_path):
    bad_market_data_path = tmp_path / "bad_market_data.json"
    bad_market_data_path.write_text(json.dumps({}), encoding="utf-8")
    config_path = _write_temp_config(tmp_path, "paper.yaml", bad_market_data_path)

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "paper summary:" in result.stdout
    assert "'errors':" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_ui_command_rejects_non_local_host_without_starting_server(tmp_path, monkeypatch, capsys):
    config_path = _write_temp_config(tmp_path, "paper.yaml")
    uvicorn = types.SimpleNamespace(run=lambda *args, **kwargs: pytest.fail("uvicorn should not start"))
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn)

    result = cli.main(["ui", "--config", str(config_path), "--host", "0.0.0.0"])

    assert result == 2
    assert "ui host must be 127.0.0.1 or localhost" in capsys.readouterr().out


def test_ui_command_starts_uvicorn_for_localhost(tmp_path, monkeypatch):
    config_path = _write_temp_config(tmp_path, "paper.yaml")
    captured = {}

    def fake_run(app, *, host, port):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setitem(sys.modules, "uvicorn", types.SimpleNamespace(run=fake_run))

    result = cli.main(["ui", "--config", str(config_path), "--host", "localhost", "--port", "8765"])

    assert result == 0
    assert captured["host"] == "localhost"
    assert captured["port"] == 8765
    assert captured["app"].state.config_path == config_path
