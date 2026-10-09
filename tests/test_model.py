
import pytest
from ml.model import predict


@pytest.mark.parametrize(
    "temperature, pressure, vibration",
    [
        (45, 80, "Low"),
        (80, 140, "Medium"),
        (105, 180, "High"),
    ],
)
def test_prediction_returns_valid_risk(
    temperature, pressure, vibration
):
    machine = {
        "temperature": temperature,
        "pressure": pressure,
        "vibration": vibration,
    }

    result = predict(machine)

    assert result in {
        "Low Risk",
        "Medium Risk",
        "High Risk",
    }


def test_prediction_is_repeatable():
    machine = {
        "temperature": 85,
        "pressure": 130,
        "vibration": "Medium",
    }

    first = predict(machine)
    second = predict(machine)

    assert first == second
