from pathlib import Path

from fastapi.testclient import TestClient

from forexbot.ui import create_app


def test_status_reports_local_host_defaults(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json()["host"] == "127.0.0.1"


def test_check_config_endpoint(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.post("/api/check-config")

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_run_once_endpoint_returns_summary(tmp_path):
    app = create_app(config_path=Path("configs/paper.yaml"), journal_path=tmp_path / "ui.jsonl")
    client = TestClient(app)

    response = client.post("/api/run-once")

    assert response.status_code == 200
    assert "executed" in response.json()["summary"]
