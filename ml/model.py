import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

FEATURES = ["temperature", "pressure", "vibration"]

def make_model():
    rng = np.random.default_rng(42)
    n = 1200
    temp = rng.uniform(20, 120, n)
    pressure = rng.uniform(50, 200, n)
    vibration = rng.choice(["Low", "Medium", "High"], n)
    score = (temp > 75).astype(int) + (temp > 95).astype(int) + (pressure > 130).astype(int) + (pressure > 165).astype(int) + (vibration == "Medium").astype(int) + 2 * (vibration == "High").astype(int)
    y = np.where(score >= 4, "High Risk", np.where(score >= 2, "Medium Risk", "Low Risk"))
    X = np.column_stack([temp, pressure, vibration])
    prep = ColumnTransformer([("categorical", OneHotEncoder(handle_unknown="ignore"), [2]), ("numbers", "passthrough", [0, 1])])
    model = Pipeline([("prep", prep), ("rf", RandomForestClassifier(n_estimators=90, random_state=42, min_samples_leaf=2))])
    model.fit(X, y)
    return model

MODEL = make_model()

def predict(values):
    row = [[float(values["temperature"]), float(values["pressure"]), values["vibration"]]]
    return str(MODEL.predict(row)[0])
