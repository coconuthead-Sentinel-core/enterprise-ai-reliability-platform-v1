"""
Real ML module.

Uses scikit-learn's IsolationForest to detect anomalous reliability
computations. This is real ML: real features, real model fit, real scores.
"""
from typing import Dict, List

import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session

from . import database

MODEL_NAME = "sklearn.IsolationForest(n_estimators=100, random_state=42)"


def detect_anomalies(
    records: List[List[float]],
    contamination: float = 0.1,
) -> Dict:
    """
    Fit an IsolationForest on the supplied records and score each one.

    Returns:
        {
          "n_trained_on", "n_scored",
          "predictions": [1 or -1, ...],    # -1 means anomaly
          "scores": [float, ...],           # higher = more normal
          "anomaly_count", "model"
        }
    """
    X = np.asarray(records, dtype=float)
    if X.ndim != 2 or X.shape[0] < 2:
        raise ValueError("records must be a 2D array with at least 2 rows")

    model = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=42,
    )
    model.fit(X)
    predictions = model.predict(X).tolist()
    scores = model.decision_function(X).tolist()

    return {
        "n_trained_on": int(X.shape[0]),
        "n_scored": int(X.shape[0]),
        "predictions": [int(p) for p in predictions],
        "scores": [float(s) for s in scores],
        "anomaly_count": int(sum(1 for p in predictions if p == -1)),
        "model": MODEL_NAME,
    }


def detect_anomalies_from_history(
    db: Session,
    contamination: float = 0.1,
) -> Dict:
    """Pull all persisted reliability computations, feed them to the model."""
    rows = db.query(database.ReliabilityComputation).all()
    if len(rows) < 2:
        raise ValueError("Need at least 2 historical records to run anomaly detection")

    X = [
        [
            r.mtbf_hours,
            r.mttr_hours,
            r.mission_time_hours,
            r.availability,
            r.reliability,
        ]
        for r in rows
    ]
    result = detect_anomalies(X, contamination)
    result["record_ids"] = [int(r.id) for r in rows]
    return result
