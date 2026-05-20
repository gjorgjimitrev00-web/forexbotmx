import os
import subprocess
import sys
from pathlib import Path


def _subprocess_env() -> dict[str, str]:
    src_path = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        path for path in (str(src_path), env.get("PYTHONPATH", "")) if path
    )
    return env


def test_check_config_command_succeeds():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "check-config", "--config", "configs/paper.yaml"],
        check=False,
        capture_output=True,
        env=_subprocess_env(),
        text=True,
    )

    assert result.returncode == 0
    assert "mode=paper" in result.stdout


def test_run_once_command_succeeds():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "run", "--config", "configs/paper.yaml", "--once"],
        check=False,
        capture_output=True,
        env=_subprocess_env(),
        text=True,
    )

    assert result.returncode == 0
    assert "executed" in result.stdout


def test_backtest_command_succeeds():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "backtest", "--config", "configs/backtest.yaml"],
        check=False,
        capture_output=True,
        env=_subprocess_env(),
        text=True,
    )

    assert result.returncode == 0
    assert "backtest summary" in result.stdout
