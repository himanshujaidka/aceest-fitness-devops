import pytest
from app import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test_aceest.sqlite3"),
    })
    with app.test_client() as test_client:
        yield test_client


def sample_client(name="Himanshu"):
    return {"name": name, "age": 24, "weight": 75, "program": "Muscle Gain"}


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ACEest Fitness" in response.data


def test_create_client_and_calculate_calories(client):
    response = client.post("/api/clients", json=sample_client())
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Himanshu"
    assert data["calories"] == 2625


def test_list_and_get_client(client):
    created = client.post("/api/clients", json=sample_client()).get_json()
    assert len(client.get("/api/clients").get_json()) == 1
    response = client.get(f"/api/clients/{created['id']}")
    assert response.status_code == 200
    assert response.get_json()["id"] == created["id"]


def test_invalid_client_payload_is_rejected(client):
    response = client.post("/api/clients", json={"name": "", "age": 24, "weight": 75, "program": "Beginner"})
    assert response.status_code == 400


def test_unknown_program_is_rejected(client):
    response = client.post("/api/clients", json={**sample_client(), "program": "Olympic Champion"})
    assert response.status_code == 400


def test_duplicate_client_returns_conflict(client):
    client.post("/api/clients", json=sample_client())
    response = client.post("/api/clients", json=sample_client())
    assert response.status_code == 409


def test_update_client_recalculates_calories(client):
    created = client.post("/api/clients", json=sample_client()).get_json()
    response = client.put(f"/api/clients/{created['id']}", json={"weight": 80})
    assert response.status_code == 200
    assert response.get_json()["calories"] == 2800


def test_delete_client(client):
    created = client.post("/api/clients", json=sample_client()).get_json()
    response = client.delete(f"/api/clients/{created['id']}")
    assert response.status_code == 200
    assert client.get(f"/api/clients/{created['id']}").status_code == 404


def test_add_and_list_progress(client):
    created = client.post("/api/clients", json=sample_client()).get_json()
    response = client.post(
        f"/api/clients/{created['id']}/progress",
        json={"week": "2026-W40", "adherence": 85},
    )
    assert response.status_code == 201
    progress = client.get(f"/api/clients/{created['id']}/progress")
    assert progress.status_code == 200
    assert progress.get_json()[0]["adherence"] == 85


def test_invalid_progress_is_rejected(client):
    created = client.post("/api/clients", json=sample_client()).get_json()
    response = client.post(
        f"/api/clients/{created['id']}/progress",
        json={"week": "2026-W40", "adherence": 101},
    )
    assert response.status_code == 400


def test_duplicate_weekly_progress_returns_conflict(client):
    created = client.post("/api/clients", json=sample_client()).get_json()
    endpoint = f"/api/clients/{created['id']}/progress"
    payload = {"week": "2026-W40", "adherence": 85}
    assert client.post(endpoint, json=payload).status_code == 201
    assert client.post(endpoint, json=payload).status_code == 409
