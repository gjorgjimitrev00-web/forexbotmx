from pathlib import Path

from fastapi.testclient import TestClient

from forexbot.ui import create_app


def test_status_reports_local_host_defaults(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["host"] == "127.0.0.1"


def test_dashboard_contains_control_panel_sections(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    body = response.text
    assert "Mode" in body
    assert "Risk" in body
    assert "Symbols" in body
    assert "Run One Cycle" in body
    assert "MT5 Live" in body


def test_check_config_endpoint(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.post("/api/check-config")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_invalid_config_save_preserves_existing_file(tmp_path):
    config_path = tmp_path / "paper.yaml"
    original = Path("configs/paper.yaml").read_text(encoding="utf-8")
    config_path.write_text(original, encoding="utf-8")
    app = create_app(config_path=config_path, journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.post("/api/config", json={"mode": "paper"})

    assert response.status_code == 400
    assert config_path.read_text(encoding="utf-8") == original


def test_run_once_endpoint_returns_summary(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.post("/api/run-once")

    assert response.status_code == 200
    assert "executed" in response.json()["summary"]
