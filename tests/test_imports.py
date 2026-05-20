import subprocess
import sys

import forexbot


def test_package_exposes_version():
    assert forexbot.__version__ == "0.1.0"


def test_module_entrypoint_shows_help():
    result = subprocess.run(
        [sys.executable, "-m", "forexbot", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "check-config" in result.stdout
    assert "backtest" in result.stdout
