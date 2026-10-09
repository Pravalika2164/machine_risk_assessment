
import json
from contextlib import contextmanager
from unittest.mock import patch

import pytest

import app as application


CORE_FIELDS = [
    {
        "id": 1,
        "name": "machine_name",
        "label": "Machine Name",
        "type": "text",
        "required": True,
        "options": [],
    },
    {
        "id": 2,
        "name": "temperature",
        "label": "Temperature",
        "type": "number",
        "required": True,
        "options": [],
    },
    {
        "id": 3,
        "name": "pressure",
        "label": "Pressure",
        "type": "number",
        "required": True,
        "options": [],
    },
    {
        "id": 4,
        "name": "vibration",
        "label": "Vibration",
        "type": "dropdown",
        "required": True,
        "options": ["Low", "Medium", "High"],
    },
]

VALID_MACHINE = {
    "machine_name": "CNC-TEST",
    "temperature": 75,
    "pressure": 40,
    "vibration": "Medium",
}


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.fetchone_result = None
        self.fetchall_result = []
        self.lastrowid = 101

    def execute(self, query, params=None):
        self.queries.append((query, params))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def executemany(self, query, values):
        self.queries.append((query, values))


@pytest.fixture
def fake_db(monkeypatch):
    cursor = FakeCursor()

    @contextmanager
    def fake_db_cursor():
        yield cursor

    # Prevent every API route from opening a real MySQL connection.
    monkeypatch.setattr(application, "db_cursor", fake_db_cursor)

    # Prevent validation from reading real MySQL field definitions.
    monkeypatch.setattr(
        application,
        "fields",
        lambda: [dict(field) for field in CORE_FIELDS],
    )

    return cursor


@pytest.fixture
def client(fake_db):
    application.app.config.update(TESTING=True)
    with application.app.test_client() as test_client:
        yield test_client


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200


def test_get_fields(client):
    response = client.get("/api/fields")

    assert response.status_code == 200
    assert len(response.get_json()) == 4


def test_create_machine(client, fake_db):
    response = client.post(
        "/api/machines",
        json=VALID_MACHINE,
    )

    assert response.status_code == 201
    assert response.get_json()["id"] == 101

    assert any(
        "INSERT INTO machines" in query
        for query, _ in fake_db.queries
    )


def test_create_machine_missing_required_field(client):
    machine = dict(VALID_MACHINE)
    del machine["temperature"]

    response = client.post("/api/machines", json=machine)

    assert response.status_code == 400
    assert "required" in response.get_json()["error"]


def test_create_machine_invalid_number(client):
    machine = dict(VALID_MACHINE)
    machine["temperature"] = "not-a-number"

    response = client.post("/api/machines", json=machine)

    assert response.status_code == 400


def test_create_machine_invalid_dropdown(client):
    machine = dict(VALID_MACHINE)
    machine["vibration"] = "Extreme"

    response = client.post("/api/machines", json=machine)

    assert response.status_code == 400


def test_create_machine_unknown_field(client):
    machine = dict(VALID_MACHINE)
    machine["unknown_parameter"] = 123

    response = client.post("/api/machines", json=machine)

    assert response.status_code == 400
    assert "Unknown fields" in response.get_json()["error"]


def test_create_machine_invalid_json(client):
    response = client.post(
        "/api/machines",
        json=["not", "an", "object"],
    )

    assert response.status_code == 400


def test_get_machines(client, fake_db):
    fake_db.fetchall_result = [
        {
            "id": 1,
            "data": json.dumps(VALID_MACHINE),
        }
    ]

    response = client.get("/api/machines")

    assert response.status_code == 200
    assert response.get_json()[0]["id"] == 1


def test_update_machine(client, fake_db):
    fake_db.fetchone_result = {"id": 1}

    response = client.put(
        "/api/machines/1",
        json=VALID_MACHINE,
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True

    assert any(
        "UPDATE machines" in query
        for query, _ in fake_db.queries
    )


def test_delete_machine(client, fake_db):
    fake_db.fetchone_result = {"id": 1}

    response = client.delete("/api/machines/1")

    assert response.status_code == 200
    assert response.get_json()["success"] is True

    assert any(
        "DELETE FROM machines" in query
        for query, _ in fake_db.queries
    )


def test_update_missing_machine(client):
    response = client.put(
        "/api/machines/999",
        json=VALID_MACHINE,
    )

    assert response.status_code == 404


def test_delete_missing_machine(client):
    response = client.delete("/api/machines/999")

    assert response.status_code == 404


def test_create_optional_field(client):
    response = client.post(
        "/api/fields",
        json={
            "label": "Humidity",
            "type": "number",
            "required": False,
        },
    )

    assert response.status_code == 201


def test_reject_required_field_when_machines_exist(client, fake_db):
    fake_db.fetchone_result = {"total": 4}

    response = client.post(
        "/api/fields",
        json={
            "label": "New Required Field",
            "type": "number",
            "required": True,
        },
    )

    assert response.status_code == 409


def test_reject_invalid_dropdown_options(client):
    response = client.post(
        "/api/fields",
        json={
            "label": "Machine Status",
            "type": "dropdown",
            "options": ["Running", "Running"],
        },
    )

    assert response.status_code == 400


def test_protect_core_field(client, fake_db):
    fake_db.fetchone_result = {
        "id": 1,
        "name": "machine_name",
        "label": "Machine Name",
        "type": "text",
        "required": 1,
        "options": "[]",
    }

    response = client.delete("/api/fields/1")

    assert response.status_code == 403


def test_delete_custom_field(client, fake_db):
    fake_db.fetchone_result = {
        "id": 6,
        "name": "humidity",
        "label": "Humidity",
        "type": "number",
        "required": 0,
        "options": "[]",
    }

    response = client.delete("/api/fields/6")

    assert response.status_code == 200

    assert any(
        "JSON_REMOVE" in query
        for query, _ in fake_db.queries
    )


def test_predict_machine(client, fake_db):
    fake_db.fetchone_result = {
        "data": json.dumps(VALID_MACHINE),
    }

    with patch.object(
        application,
        "predict",
        return_value="Medium Risk",
    ) as mock_predict:
        response = client.post("/api/predict/1")

    assert response.status_code == 200
    assert response.get_json()["risk"] == "Medium Risk"
    mock_predict.assert_called_once()


def test_predict_missing_machine(client):
    response = client.post("/api/predict/999")

    assert response.status_code == 404


def test_predict_missing_features(client, fake_db):
    machine = dict(VALID_MACHINE)
    del machine["temperature"]

    fake_db.fetchone_result = {
        "data": json.dumps(machine),
    }

    response = client.post("/api/predict/1")

    assert response.status_code == 400
