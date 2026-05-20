import json
import os
import subprocess
import sys
from pathlib import Path


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


def test_run_rejects_mt5_demo_mode_without_traceback(tmp_path):
    config_path = _write_temp_config_with_mode(tmp_path, "paper.yaml", "mt5_demo")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "MT5 demo execution is disabled in V1" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_run_rejects_backtest_mode_without_traceback(tmp_path):
    config_path = _write_temp_config(tmp_path, "backtest.yaml")

    result = _run_cli(["run", "--config", str(config_path), "--once"], tmp_path)

    assert result.returncode != 0
    assert "run requires mode=paper" in result.stdout
    assert "Traceback" not in result.stdout
    assert "Traceback" not in result.stderr


def test_backtest_command_succeeds(tmp_path):
    config_path = _write_temp_config(tmp_path, "backtest.yaml")

    result = _run_cli(["backtest", "--config", str(config_path)], tmp_path)

    assert result.returncode == 0
    assert "backtest summary" in result.stdout
    assert (tmp_path / "journals" / "backtest.jsonl").exists()


def test_backtest_rejects_mt5_demo_mode_without_traceback(tmp_path):
    config_path = _write_temp_config_with_mode(tmp_path, "backtest.yaml", "mt5_demo")

    result = _run_cli(["backtest", "--config", str(config_path)], tmp_path)

    assert result.returncode != 0
    assert "MT5 demo execution is disabled in V1" in result.stdout
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
