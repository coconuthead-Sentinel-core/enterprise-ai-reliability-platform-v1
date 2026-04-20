"""
Full-build integration test (v0.3.0).
Real FastAPI app, real SQLite DB, real math, real bcrypt, real JWT,
real scikit-learn IsolationForest. No mocks.

Run:   python test_backend.py     (from the enterprise_ai_backend/ folder)
"""
import hashlib
import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_TMP_DB = os.path.join(tempfile.gettempdir(), "enterprise_ai_test_v3.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["JWT_SECRET"] = "test-secret-" + "z" * 48

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402

init_db()
client = TestClient(app)

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(name, cond, detail=""):
    status = PASS if cond else FAIL
    print(f"  [{status}] {name}{(' - ' + detail) if detail else ''}")
    results.append((name, cond))
    assert cond, f"FAILED: {name} - {detail}"


def section(title):
    print("\n" + "-" * 72)
    print(title)
    print("-" * 72)


def main():
    results.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("=" * 72)
    print("EARP FULL BUILD INTEGRATION TEST (v0.3.0)")
    print("Real FastAPI, real SQLite, real bcrypt + JWT, real scikit-learn")
    print("=" * 72)

    # ---------- 1. Root + health ----------
    section("1. GET /")
    r = client.get("/")
    check("root 200", r.status_code == 200)
    check("app name", r.json()["app"] == "enterprise_ai_backend")

    section("2. GET /health")
    r = client.get("/health")
    check("health 200", r.status_code == 200)
    h = r.json()
    check("db ok", h["database"] == "ok")
    check("uptime >= 0", h["uptime_seconds"] >= 0)

    # ---------- 3. Auth: register, login, me ----------
    section("3. POST /auth/register")
    r = client.post("/auth/register", json={
        "email": "shannon@example.com", "password": "correcthorsebatterystaple",
    })
    check("register 201", r.status_code == 201, r.text)
    user = r.json()
    check("user has id", isinstance(user["id"], int))
    check("email lowercased", user["email"] == "shannon@example.com")
    check("default role = user", user["role"] == "user")

    r_dup = client.post("/auth/register", json={
        "email": "shannon@example.com", "password": "anotherpassword",
    })
    check("duplicate email rejected 400", r_dup.status_code == 400)

    r_weak = client.post("/auth/register", json={
        "email": "weak@example.com", "password": "short",
    })
    check("short password rejected 422", r_weak.status_code == 422)

    r_bad = client.post("/auth/register", json={
        "email": "notanemail", "password": "correcthorsebatterystaple",
    })
    check("bad email rejected 422", r_bad.status_code == 422)

    section("4. POST /auth/login")
    r = client.post("/auth/login", json={
        "email": "shannon@example.com", "password": "correcthorsebatterystaple",
    })
    check("login 200", r.status_code == 200, r.text)
    tok = r.json()
    check("got access_token", "access_token" in tok and len(tok["access_token"]) > 20)
    check("token_type bearer", tok["token_type"] == "bearer")
    check("expires_in > 0", tok["expires_in"] > 0)
    TOKEN = tok["access_token"]

    r_bad = client.post("/auth/login", json={
        "email": "shannon@example.com", "password": "wrong",
    })
    check("wrong password 401", r_bad.status_code == 401)

    section("5. GET /auth/me (authenticated)")
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {TOKEN}"})
    check("me 200", r.status_code == 200)
    check("me email matches", r.json()["email"] == "shannon@example.com")

    r = client.get("/auth/me")
    check("no token -> 401", r.status_code == 401)

    r = client.get("/auth/me", headers={"Authorization": "Bearer not.a.real.token"})
    check("bad token -> 401", r.status_code == 401)

    # ---------- 6. Reliability (public) ----------
    section("6. POST /reliability/compute (seeding history)")
    r = client.post("/reliability/compute",
                    json={"mtbf_hours": 1000, "mttr_hours": 4, "mission_time_hours": 720})
    check("compute 200", r.status_code == 200)
    b = r.json()
    exp_avail = 1000 / 1004
    exp_rel = math.exp(-0.72)
    check("availability real", abs(b["availability"] - exp_avail) < 1e-6)
    check("reliability real", abs(b["reliability"] - exp_rel) < 1e-6)

    for mtbf, mttr, mission in [
        (50000, 2, 8760), (2000, 6, 720), (500, 10, 720),
        (1500, 5, 720), (20, 2, 100),  # <-- the odd one out (tiny MTBF)
    ]:
        rr = client.post("/reliability/compute",
                         json={"mtbf_hours": mtbf, "mttr_hours": mttr,
                               "mission_time_hours": mission})
        check(f"seed mtbf={mtbf}", rr.status_code == 200)

    r = client.get("/reliability/history")
    check("history 200", r.status_code == 200)
    check("history has 6+ rows", len(r.json()) >= 6, f"got {len(r.json())}")

    # ---------- 7. Assessments now require auth ----------
    section("7. POST /assessments requires auth")
    r = client.post("/assessments", json={
        "system_name": "X", "owner": "Y",
        "govern_score": 80, "map_score": 80, "measure_score": 80, "manage_score": 80,
    })
    check("unauthenticated -> 401", r.status_code == 401)

    hdr = {"Authorization": f"Bearer {TOKEN}"}
    r = client.post("/assessments", json={
        "system_name": "Claims Triage Model", "owner": "Shannon Brian Kelly",
        "govern_score": 85, "map_score": 78, "measure_score": 72, "manage_score": 81,
        "notes": "Baseline",
    }, headers=hdr)
    check("assessment created 201", r.status_code == 201)
    asm = r.json()
    check("overall = 79.0", abs(asm["overall_score"] - 79.0) < 1e-6)
    check("tier = MEDIUM", asm["risk_tier"] == "MEDIUM")

    # ---------- 8. AI: IsolationForest on real numbers ----------
    section("8. POST /ai/anomaly-detect (scikit-learn IsolationForest)")
    # Unauthenticated call is rejected before we get to validation
    r = client.post("/ai/anomaly-detect",
                    json={"records": [[1, 2, 3], [4, 5, 6]], "contamination": 0.1})
    check("unauthenticated anomaly-detect -> 401", r.status_code == 401)

    # Authenticated call with empty records fails schema validation
    r = client.post("/ai/anomaly-detect",
                    json={"records": [], "contamination": 0.1},
                    headers={"Authorization": f"Bearer {TOKEN}"})
    check("empty records -> 422", r.status_code == 422, r.text)

    payload = {
        "records": [
            # 10 'normal' servers clustered together
            *[[1000 + i, 4, 720, 0.996, 0.487] for i in range(10)],
            # one obvious outlier
            [50, 40, 720, 0.55, 0.05],
        ],
        "contamination": 0.1,
    }
    r = client.post("/ai/anomaly-detect", json=payload, headers=hdr)
    check("anomaly-detect 200", r.status_code == 200, r.text)
    body = r.json()
    check("trained on 11", body["n_trained_on"] == 11)
    check("predictions length 11", len(body["predictions"]) == 11)
    check("anomaly_count >= 1", body["anomaly_count"] >= 1,
          f"got {body['anomaly_count']}")
    # Last row is the outlier - should be flagged
    check("outlier flagged (last prediction = -1)",
          body["predictions"][-1] == -1,
          f"preds={body['predictions']}")
    check("uses real IsolationForest",
          "IsolationForest" in body["model"])

    section("9. GET /ai/anomaly-detect/from-history")
    r = client.get("/ai/anomaly-detect/from-history?contamination=0.2", headers=hdr)
    check("from-history 200", r.status_code == 200, r.text)
    body = r.json()
    check("trained on >=6 history rows",
          body["n_trained_on"] >= 6, f"got {body['n_trained_on']}")
    check("record_ids returned", body.get("record_ids") is not None)
    check("at least one anomaly found", body["anomaly_count"] >= 1)

    r = client.get("/ai/anomaly-detect/from-history")
    check("unauthenticated -> 401", r.status_code == 401)

    # ---------- 10. Hash + validation ----------
    section("10. POST /hash/sha256")
    text = "Enterprise AI Reliability Platform v1"
    r = client.post("/hash/sha256", json={"text": text})
    check("hash 200", r.status_code == 200)
    exp_hash = hashlib.sha256(text.encode()).hexdigest()
    check("matches hashlib.sha256", r.json()["sha256"] == exp_hash)

    # ---------- 11. Info endpoints (public, read-only) ----------
    section("11. GET /info/epics and /info/sprint")
    r = client.get("/info/epics")
    check("info/epics 200", r.status_code == 200)
    epics = r.json()
    check("5 epics returned", len(epics) == 5, f"got {len(epics)}")
    check("first epic is E1", epics[0]["id"] == "E1")
    check("E1 in_progress", epics[0]["status"] == "in_progress")
    check("E2 in_progress (Sprint 2 active)", epics[1]["status"] == "in_progress")
    check("every epic has title", all(e.get("title") for e in epics))
    check("every epic has int sprint", all(isinstance(e["sprint"], int) for e in epics))
    check("epic statuses are valid",
          all(e["status"] in {"not_started", "in_progress", "done"} for e in epics))

    r = client.get("/info/sprint")
    check("info/sprint 200", r.status_code == 200)
    s = r.json()
    check("current_sprint is 2", s["current_sprint"] == 2)
    check("total_sprints is 5", s["total_sprints"] == 5)
    check("release is v0.3.0", s["release"] == "v0.3.0")
    check("E2 is now in_progress", next(e for e in epics if e["id"] == "E2")["status"] == "in_progress")

    # ---------- 12. Reliability composite score (Sprint 2, E2-S1) ----------
    section("12. POST /reliability/score (weighted composite + NIST breakdown)")

    # Happy path: 3 components, weights sum to 1.0
    r = client.post("/reliability/score", json={
        "system_name": "Claims Triage Model",
        "components": [
            {"name": "availability", "value": 0.996, "weight": 0.4,
             "nist_function": "measure"},
            {"name": "governance", "value": 0.85, "weight": 0.3,
             "nist_function": "govern"},
            {"name": "security_posture", "value": 0.75, "weight": 0.3,
             "nist_function": "manage"},
        ],
    })
    check("score 200", r.status_code == 200, r.text)
    body = r.json()
    check("system_name echoed", body["system_name"] == "Claims Triage Model")
    # 0.996*0.4 + 0.85*0.3 + 0.75*0.3 = 0.3984 + 0.255 + 0.225 = 0.8784 -> 87.84
    check("composite_score ~87.84",
          abs(body["composite_score"] - 87.84) < 0.01,
          f"got {body['composite_score']}")
    check("tier LOW (>=80)", body["tier"] == "LOW")
    check("weights_normalized False (weights sum to 1.0)",
          body["weights_normalized"] is False)
    check("nist govern = 85.0",
          abs(body["nist_breakdown"]["govern"] - 85.0) < 0.01)
    check("nist measure = 99.6",
          abs(body["nist_breakdown"]["measure"] - 99.6) < 0.01)
    check("nist manage = 75.0",
          abs(body["nist_breakdown"]["manage"] - 75.0) < 0.01)
    check("nist map is null (no components tagged)",
          body["nist_breakdown"]["map"] is None)
    check("components echoed", len(body["components"]) == 3)

    # Unnormalized weights - should be normalized automatically
    r = client.post("/reliability/score", json={
        "system_name": "Unnormalized",
        "components": [
            {"name": "a", "value": 1.0, "weight": 1.0},
            {"name": "b", "value": 0.5, "weight": 1.0},
        ],
    })
    check("unnormalized weights 200", r.status_code == 200)
    body = r.json()
    check("weights_normalized True", body["weights_normalized"] is True)
    # (1.0*1.0 + 0.5*1.0) / 2.0 = 0.75 -> 75.0
    check("composite normalized = 75.0",
          abs(body["composite_score"] - 75.0) < 0.01)
    check("tier MEDIUM", body["tier"] == "MEDIUM")

    # Tier HIGH (low composite)
    r = client.post("/reliability/score", json={
        "system_name": "Low",
        "components": [{"name": "bad", "value": 0.3, "weight": 1.0}],
    })
    check("low score tier HIGH", r.json()["tier"] == "HIGH")

    # Validation: empty component list -> 422
    r = client.post("/reliability/score",
                    json={"system_name": "E", "components": []})
    check("empty components -> 422", r.status_code == 422)

    # Validation: value > 1.0 -> 422
    r = client.post("/reliability/score", json={
        "system_name": "E",
        "components": [{"name": "x", "value": 1.5, "weight": 1.0}],
    })
    check("value > 1.0 -> 422", r.status_code == 422)

    # Validation: weight = 0 -> 422
    r = client.post("/reliability/score", json={
        "system_name": "E",
        "components": [{"name": "x", "value": 0.5, "weight": 0.0}],
    })
    check("weight = 0 -> 422", r.status_code == 422)

    # ---------- Summary ----------
    section("SUMMARY")
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"  {passed}/{total} assertions passed")
    assert passed == total
    print("\n" + "=" * 72)
    print("FULL BUILD TESTS PASSED - REAL AUTH, REAL ML, REAL NUMBERS")
    print("=" * 72)


def test_full_build_integration():
    main()


if __name__ == "__main__":
    main()
