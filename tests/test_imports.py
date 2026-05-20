import os
import subprocess
import sys
from pathlib import Path

import forexbot


def test_package_exposes_version():
    assert forexbot.__version__ == "0.1.0"


def test_module_entrypoint_shows_help():
    src_path = Path(__file__).resolve().parents[1] / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        path for path in (str(src_path), env.get("PYTHONPATH", "")) if path
    )

    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "--help"],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0
    assert "check-config" in result.stdout
    assert "backtest" in result.stdout
