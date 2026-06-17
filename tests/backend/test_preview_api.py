"""Tests for preview-serving API endpoints."""

import os

from fastapi.testclient import TestClient

from backend import main
from backend.config import settings
from backend.core.state_store import StateStore
from backend.tools.file_manager import FileManager


def _make_client(tmp_path, monkeypatch):
    output_dir = str(tmp_path)
    monkeypatch.setattr(settings, "output_dir", output_dir)
    main.state_store = StateStore(base_dir=os.path.join(output_dir, "states"))
    client = TestClient(main.app)
    return client, main.state_store, output_dir


def _create_web_project(
    state_store,
    output_dir,
    project_id="web1",
    *,
    html='<link rel="stylesheet" href="style.css">',
    css="body { color: red; }\n",
):
    state_store.create_project(project_id, "Build a static web app")
    state_store.update_workflow_profile(project_id, "static_web")
    state_store.update_artifact_status(
        project_id,
        {
            "type": "static_web",
            "status": "ready",
            "preview_url": f"/api/projects/{project_id}/preview/",
            "issues": [],
        },
    )
    file_manager = FileManager(base_dir=os.path.join(output_dir, project_id))
    file_manager.write_file("index.html", html)
    file_manager.write_file("style.css", css)


def test_preview_root_serves_index_html(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "style.css" in response.text


def test_preview_asset_serves_css_file(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    css = "body { color: red; }\n"
    _create_web_project(state_store, output_dir, css=css)

    response = client.get("/api/projects/web1/preview/style.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert response.text == css


def test_preview_missing_asset_returns_404(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/missing.js")

    assert response.status_code == 404
    assert response.json()["detail"] == "Preview file missing.js not found"


def test_preview_blocks_parent_traversal(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/../states/web1.json")

    assert response.status_code in {403, 404}


def test_preview_blocks_dotfiles(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1/preview/.secret")

    assert response.status_code == 403


def test_preview_rejects_non_ready_projects(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    state_store.create_project("cli1", "Build a CLI")
    state_store.update_workflow_profile("cli1", "default")
    state_store.update_artifact_status(
        "cli1",
        {
            "type": "none",
            "status": "unknown",
            "preview_url": "",
            "issues": [],
        },
    )

    response = client.get("/api/projects/cli1/preview/")

    assert response.status_code == 409
    assert response.json()["detail"] == "Project cli1 is not preview-ready"


def test_get_project_includes_profile_and_artifact_status(tmp_path, monkeypatch):
    client, state_store, output_dir = _make_client(tmp_path, monkeypatch)
    _create_web_project(state_store, output_dir)

    response = client.get("/api/projects/web1")

    assert response.status_code == 200
    assert response.json()["workflow_profile"] == "static_web"
    assert response.json()["artifact_status"] == {
        "type": "static_web",
        "status": "ready",
        "preview_url": "/api/projects/web1/preview/",
        "issues": [],
    }
