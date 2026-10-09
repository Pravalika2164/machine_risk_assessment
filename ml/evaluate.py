
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

from ml.model import MODEL


def evaluate_model():
    # Generate a separate synthetic evaluation dataset.
    rng = np.random.default_rng(123)
    n = 300

    temp = rng.uniform(20, 120, n)
    pressure = rng.uniform(50, 200, n)
    vibration = rng.choice(["Low", "Medium", "High"], n)

    # Use the same labeling rules as ml/model.py.
    score = (
        (temp > 75).astype(int)
        + (temp > 95).astype(int)
        + (pressure > 130).astype(int)
        + (pressure > 165).astype(int)
        + (vibration == "Medium").astype(int)
        + 3 * (vibration == "High").astype(int)
    )

    y_true = np.where(
        score >= 4,
        "High Risk",
        np.where(score >= 2, "Medium Risk", "Low Risk"),
    )

    X_test = np.column_stack([temp, pressure, vibration])
    y_pred = MODEL.predict(X_test)

    labels = ["Low Risk", "Medium Risk", "High Risk"]

    print("\nMODEL EVALUATION")
    print("----------------------------------------")
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_true,
            y_pred,
            labels=labels,
            zero_division=0,
        )
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred, labels=labels))
    print("\nClass order:", labels)


if __name__ == "__main__":
    evaluate_model()
