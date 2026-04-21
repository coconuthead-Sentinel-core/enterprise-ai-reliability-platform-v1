"""
Full-build integration test (v0.3.0).
Real FastAPI app, real SQLite DB, real math, real bcrypt, real JWT,
real scikit-learn IsolationForest. No mocks.

Run:   python test_backend.py     (from the enterprise_ai_backend/ folder)
"""
import atexit
import hashlib
import io
import json
import math
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use a unique temp directory for each run so interrupted sessions do not leave
# behind a reused SQLite file that can collide with the next invocation.
_TMP_DIR = tempfile.mkdtemp(prefix="enterprise_ai_test_v3-")
atexit.register(lambda: shutil.rmtree(_TMP_DIR, ignore_errors=True))
_TMP_DB = os.path.join(_TMP_DIR, "enterprise_ai_test_v3.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["JWT_SECRET"] = "test-secret-" + "z" * 48

from fastapi.testclient import TestClient  # noqa: E402
from pypdf import PdfReader  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import (  # noqa: E402
    AuditLogRecord,
    Base,
    ReleaseApproval,
    SessionLocal,
    User,
    engine,
    init_db,
)
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


def set_role(email: str, role: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email=email).first()
        assert user is not None, f"User not found for role update: {email}"
        user.role = role
        db.add(user)
        db.commit()
    finally:
        db.close()


def clear_release_approvals():
    db = SessionLocal()
    try:
        db.query(ReleaseApproval).delete()
        db.commit()
    finally:
        db.close()


def force_tamper_audit_record(record_id: int):
    with engine.begin() as conn:
        conn.execute(text("DROP TRIGGER IF EXISTS audit_log_records_no_update"))
        conn.execute(text("DROP TRIGGER IF EXISTS audit_log_records_no_delete"))
        conn.execute(
            text(
                "UPDATE audit_log_records "
                "SET payload_json = :payload "
                "WHERE id = :record_id"
            ),
            {
                "payload": json.dumps({"tampered": True}, sort_keys=True),
                "record_id": record_id,
            },
        )
    init_db()


def main():
    results.clear()
    Base.metadata.drop_all(bind=engine)
    init_db()

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
    # Sprint 3, E3-S2: the gate rides along with every assessment now.
    # 79.0 is in the [60, 80) warn band and every NIST function is >= 40
    # so overall decision must be 'warn'.
    check("gate_decision = warn (E3-S2)",
          asm.get("gate_decision") == "warn",
          f"got {asm.get('gate_decision')}")
    check("gate_reasons non-empty (E3-S2)",
          isinstance(asm.get("gate_reasons"), list) and len(asm["gate_reasons"]) >= 1)

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
    check("E2 done (Sprint 2 complete)", epics[1]["status"] == "done")
    check("E3 done (Sprint 3 delivered)", epics[2]["status"] == "done")
    check("E4 in_progress (Sprint 4 local build)", epics[3]["status"] == "in_progress")
    check("E5 in_progress (Sprint 5 evidence slice)", epics[4]["status"] == "in_progress")
    check("every epic has title", all(e.get("title") for e in epics))
    check("every epic has int sprint", all(isinstance(e["sprint"], int) for e in epics))
    check("epic statuses are valid",
          all(e["status"] in {"not_started", "in_progress", "done"} for e in epics))

    r = client.get("/info/sprint")
    check("info/sprint 200", r.status_code == 200)
    s = r.json()
    check("current_sprint is 4", s["current_sprint"] == 4)
    check("total_sprints is 5", s["total_sprints"] == 5)
    check("release is v0.3.0", s["release"] == "v0.3.0")
    check("E2 is done (Epic E2 shipped in Sprint 2)",
          next(e for e in epics if e["id"] == "E2")["status"] == "done")
    check("E3 is done (Sprint 3 delivered)",
          next(e for e in epics if e["id"] == "E3")["status"] == "done")

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

    # ---------- 13. Reliability score explanation (Sprint 2, E2-S2) ----------
    section("13. POST /reliability/score/explain (composite + explanation)")

    explain_payload = {
        "system_name": "Claims Triage Model",
        "components": [
            {"name": "availability", "value": 0.996, "weight": 0.4,
             "nist_function": "measure"},
            {"name": "governance", "value": 0.85, "weight": 0.3,
             "nist_function": "govern"},
            {"name": "security_posture", "value": 0.75, "weight": 0.3,
             "nist_function": "manage"},
        ],
    }
    r = client.post("/reliability/score/explain", json=explain_payload)
    check("score/explain 200", r.status_code == 200, r.text)
    body = r.json()
    check("explain echoes system_name",
          body["system_name"] == "Claims Triage Model")
    check("explain composite ~87.84",
          abs(body["composite_score"] - 87.84) < 0.01,
          f"got {body['composite_score']}")
    check("explain tier LOW", body["tier"] == "LOW")
    check("explain nist measure = 99.6",
          abs(body["nist_breakdown"]["measure"] - 99.6) < 0.01)

    explanation = body["explanation"]
    check("explanation present", isinstance(explanation, dict))
    contribs = explanation["contributions"]
    check("3 contributions returned", len(contribs) == 3)
    # Contributions are sorted highest-first.
    check("contributions sorted desc",
          contribs[0]["contribution"] >= contribs[1]["contribution"]
          >= contribs[2]["contribution"])
    # Availability (0.996 * 0.4 = 0.3984 -> 39.84) drives the score hardest.
    check("top_driver is availability",
          explanation["top_driver"]["component_name"] == "availability")
    check("top_driver contribution ~39.84",
          abs(explanation["top_driver"]["contribution"] - 39.84) < 0.01,
          f"got {explanation['top_driver']['contribution']}")
    # security_posture has the lowest value (0.75).
    check("top_gap is security_posture",
          explanation["top_gap"]["component_name"] == "security_posture")
    # Contributions on the 0-100 scale should sum to the composite score.
    total_contrib = sum(c["contribution"] for c in contribs)
    check("sum(contributions) ~= composite",
          abs(total_contrib - body["composite_score"]) < 0.01,
          f"sum={total_contrib} composite={body['composite_score']}")
    # contribution_percent sums to 100 (allow small float drift).
    total_pct = sum(c["contribution_percent"] for c in contribs)
    check("sum(contribution_percent) ~= 100",
          abs(total_pct - 100.0) < 0.05,
          f"sum={total_pct}")
    # Tier gap for LOW: no tier-up, MEDIUM below with buffer = composite - 80.
    tg = explanation["tier_gap"]
    check("tier_gap current_tier LOW", tg["current_tier"] == "LOW")
    check("tier_gap no tier_up", tg["next_tier_up"] is None)
    check("tier_gap no points_needed_up", tg["points_needed_up"] is None)
    check("tier_gap next_tier_down MEDIUM",
          tg["next_tier_down"] == "MEDIUM")
    check("tier_gap buffer ~7.84",
          abs(tg["points_buffer_down"] - 7.84) < 0.01,
          f"got {tg['points_buffer_down']}")
    # measure > govern > manage, so weakest = manage, strongest = measure.
    check("weakest_nist_function = manage",
          explanation["weakest_nist_function"] == "manage")
    check("strongest_nist_function = measure",
          explanation["strongest_nist_function"] == "measure")
    check("recommendation non-empty",
          isinstance(explanation["recommendation"], str)
          and len(explanation["recommendation"]) > 10)

    # Single-component edge case.
    r = client.post("/reliability/score/explain", json={
        "system_name": "Solo",
        "components": [{"name": "only", "value": 0.6, "weight": 1.0}],
    })
    check("single-component explain 200", r.status_code == 200)
    body = r.json()
    check("single-component tier MEDIUM", body["tier"] == "MEDIUM")
    check("single-component only one contribution",
          len(body["explanation"]["contributions"]) == 1)
    check("single-component top_driver == top_gap",
          body["explanation"]["top_driver"]["component_name"]
          == body["explanation"]["top_gap"]["component_name"])
    # MEDIUM tier-gap: needs (80 - 60) = 20 points up, buffer of 0 down.
    tg = body["explanation"]["tier_gap"]
    check("MEDIUM tier_gap next_tier_up LOW",
          tg["next_tier_up"] == "LOW")
    check("MEDIUM tier_gap needs 20 points",
          abs(tg["points_needed_up"] - 20.0) < 0.01,
          f"got {tg['points_needed_up']}")
    check("MEDIUM tier_gap next_tier_down HIGH",
          tg["next_tier_down"] == "HIGH")
    # No NIST function tagged -> weakest/strongest are null.
    check("solo weakest_nist_function null",
          body["explanation"]["weakest_nist_function"] is None)

    # HIGH-tier path: composite well below 60.
    r = client.post("/reliability/score/explain", json={
        "system_name": "Struggling",
        "components": [
            {"name": "bad_governance", "value": 0.3, "weight": 0.5,
             "nist_function": "govern"},
            {"name": "bad_security", "value": 0.2, "weight": 0.5,
             "nist_function": "manage"},
        ],
    })
    check("HIGH-tier explain 200", r.status_code == 200)
    body = r.json()
    check("HIGH-tier tier HIGH", body["tier"] == "HIGH")
    tg = body["explanation"]["tier_gap"]
    check("HIGH-tier no next_tier_down", tg["next_tier_down"] is None)
    check("HIGH-tier points_needed_up > 0",
          tg["points_needed_up"] is not None and tg["points_needed_up"] > 0)
    check("HIGH-tier recommendation mentions HIGH",
          "HIGH" in body["explanation"]["recommendation"])

    # Validation: empty components still rejected at schema layer.
    r = client.post("/reliability/score/explain",
                    json={"system_name": "E", "components": []})
    check("explain empty components -> 422", r.status_code == 422)

    # ---------- 14. Reliability score history (Sprint 2, E2-S3) ----------
    section("14. GET /reliability/score/history (persistence + trend stats)")

    # Every /reliability/score and /reliability/score/explain call above
    # already persists a record. Empty-system filter should see zero.
    r = client.get("/reliability/score/history?system_name=NoSuchSystem")
    check("filter no match 200", r.status_code == 200)
    body = r.json()
    check("no-match returns empty records", body["records"] == [])
    check("no-match count is 0", body["stats"]["count"] == 0)
    check("no-match trend is insufficient_data",
          body["stats"]["trend_direction"] == "insufficient_data")
    check("no-match transitions empty",
          body["stats"]["tier_transitions"] == [])

    # Post a controlled history for "Trending System": HIGH -> MEDIUM -> LOW.
    for components in [
        [{"name": "bad", "value": 0.3, "weight": 1.0}],               # 30 -> HIGH
        [{"name": "meh", "value": 0.65, "weight": 1.0}],              # 65 -> MEDIUM
        [{"name": "good", "value": 0.9, "weight": 1.0}],              # 90 -> LOW
    ]:
        rr = client.post("/reliability/score", json={
            "system_name": "Trending System",
            "components": components,
        })
        check(f"seed value={components[0]['value']}", rr.status_code == 200)

    r = client.get("/reliability/score/history?system_name=Trending%20System")
    check("trending history 200", r.status_code == 200)
    body = r.json()
    check("trending filter echoed",
          body["system_name"] == "Trending System")
    check("trending count = 3", body["stats"]["count"] == 3,
          f"got {body['stats']['count']}")
    check("trending records length 3", len(body["records"]) == 3)
    # Newest-first: record[0] should be the LOW (90) score.
    check("trending newest-first (90 first)",
          abs(body["records"][0]["composite_score"] - 90.0) < 0.01,
          f"got {body['records'][0]['composite_score']}")
    check("trending newest tier LOW",
          body["records"][0]["tier"] == "LOW")
    check("trending oldest (30) last",
          abs(body["records"][-1]["composite_score"] - 30.0) < 0.01)

    stats = body["stats"]
    check("trending latest_score = 90",
          abs(stats["latest_score"] - 90.0) < 0.01)
    check("trending latest_tier LOW", stats["latest_tier"] == "LOW")
    check("trending earliest_score = 30",
          abs(stats["earliest_score"] - 30.0) < 0.01)
    check("trending earliest_tier HIGH", stats["earliest_tier"] == "HIGH")
    # Rolling average = (30 + 65 + 90) / 3 = 61.666...
    check("trending rolling_average ~61.67",
          abs(stats["rolling_average"] - 61.6667) < 0.01,
          f"got {stats['rolling_average']}")
    check("trending min_score = 30",
          abs(stats["min_score"] - 30.0) < 0.01)
    check("trending max_score = 90",
          abs(stats["max_score"] - 90.0) < 0.01)
    # Monotonically increasing scores -> improving.
    check("trending direction improving",
          stats["trend_direction"] == "improving",
          f"got {stats['trend_direction']}")
    # HIGH -> MEDIUM and MEDIUM -> LOW are the two transitions.
    check("trending 2 transitions",
          len(stats["tier_transitions"]) == 2,
          f"got {len(stats['tier_transitions'])}")
    transitions = stats["tier_transitions"]
    # Transitions are in chronological order.
    check("first transition HIGH -> MEDIUM",
          transitions[0]["from_tier"] == "HIGH"
          and transitions[0]["to_tier"] == "MEDIUM")
    check("second transition MEDIUM -> LOW",
          transitions[1]["from_tier"] == "MEDIUM"
          and transitions[1]["to_tier"] == "LOW")

    # Degrading system.
    for v in [0.95, 0.7, 0.4]:
        client.post("/reliability/score", json={
            "system_name": "Degrading System",
            "components": [{"name": "x", "value": v, "weight": 1.0}],
        })
    r = client.get("/reliability/score/history?system_name=Degrading%20System")
    check("degrading direction degrading",
          r.json()["stats"]["trend_direction"] == "degrading")

    # Stable system (all within 1 composite point).
    for v in [0.85, 0.855, 0.852]:
        client.post("/reliability/score", json={
            "system_name": "Stable System",
            "components": [{"name": "x", "value": v, "weight": 1.0}],
        })
    r = client.get("/reliability/score/history?system_name=Stable%20System")
    check("stable direction stable",
          r.json()["stats"]["trend_direction"] == "stable")
    check("stable 0 transitions",
          len(r.json()["stats"]["tier_transitions"]) == 0)

    # /reliability/score/explain ALSO persists (one call per payload).
    before = client.get("/reliability/score/history"
                        "?system_name=Explain%20Persist").json()["stats"]["count"]
    client.post("/reliability/score/explain", json={
        "system_name": "Explain Persist",
        "components": [{"name": "x", "value": 0.8, "weight": 1.0}],
    })
    after = client.get("/reliability/score/history"
                       "?system_name=Explain%20Persist").json()["stats"]["count"]
    check("score/explain persists a row", after == before + 1,
          f"before={before} after={after}")

    # No-filter global history returns at least all the systems we seeded.
    r = client.get("/reliability/score/history?limit=200")
    check("global history 200", r.status_code == 200)
    body = r.json()
    check("global system_name null", body["system_name"] is None)
    check("global count >= 10", body["stats"]["count"] >= 10,
          f"got {body['stats']['count']}")

    # Limit param clamps the response.
    r = client.get("/reliability/score/history?limit=2")
    check("limit=2 returns 2 records", len(r.json()["records"]) == 2)

    # Validation: limit outside [1, 500] rejected.
    r = client.get("/reliability/score/history?limit=0")
    check("limit=0 -> 422", r.status_code == 422)
    r = client.get("/reliability/score/history?limit=501")
    check("limit=501 -> 422", r.status_code == 422)

    # ---------- 15. Policy gate evaluation (Sprint 3, E3-S1) ----------
    section("15. POST /policy/evaluate (allow / warn / block)")

    # ALLOW path: composite 87.84 >= 80, all NIST functions well above floor.
    r = client.post("/policy/evaluate", json={
        "score_input": {
            "system_name": "Claims Triage Model",
            "components": [
                {"name": "availability", "value": 0.996, "weight": 0.4,
                 "nist_function": "measure"},
                {"name": "governance", "value": 0.85, "weight": 0.3,
                 "nist_function": "govern"},
                {"name": "security_posture", "value": 0.75, "weight": 0.3,
                 "nist_function": "manage"},
            ],
        },
    })
    check("policy/evaluate 200", r.status_code == 200, r.text)
    body = r.json()
    check("allow decision", body["decision"] == "allow",
          f"got {body['decision']}")
    check("composite echoed (~87.84)",
          abs(body["composite_score"] - 87.84) < 0.01)
    check("tier LOW on allow", body["tier"] == "LOW")
    check("allow has 1 info reason",
          len(body["reasons"]) == 1
          and body["reasons"][0]["severity"] == "info")
    check("allow reason code composite_meets_allow",
          body["reasons"][0]["code"] == "composite_meets_allow")
    check("default thresholds echoed",
          body["thresholds_applied"]["allow_min_composite"] == 80.0)

    # WARN path: composite 75 is between 60 (warn) and 80 (allow).
    r = client.post("/policy/evaluate", json={
        "score_input": {
            "system_name": "Medium",
            "components": [{"name": "x", "value": 0.75, "weight": 1.0}],
        },
    })
    check("warn 200", r.status_code == 200)
    body = r.json()
    check("warn decision", body["decision"] == "warn",
          f"got {body['decision']}")
    check("warn tier MEDIUM", body["tier"] == "MEDIUM")
    # With no NIST function tagged, only the composite rule fires -> 1 warn.
    check("warn 1 reason", len(body["reasons"]) == 1)
    check("warn reason code",
          body["reasons"][0]["code"] == "composite_below_allow")
    check("warn reason severity",
          body["reasons"][0]["severity"] == "warn")

    # BLOCK path: composite 30 < 60.
    r = client.post("/policy/evaluate", json={
        "score_input": {
            "system_name": "Bad",
            "components": [{"name": "x", "value": 0.3, "weight": 1.0}],
        },
    })
    check("block 200", r.status_code == 200)
    body = r.json()
    check("block decision", body["decision"] == "block")
    check("block tier HIGH", body["tier"] == "HIGH")
    check("block reason severity",
          body["reasons"][0]["severity"] == "block")
    check("block reason code",
          body["reasons"][0]["code"] == "composite_below_warn")

    # NIST FLOOR trumps: composite passes allow (85) but a NIST function
    # comes in below the min_nist_function_score floor -> block overall.
    r = client.post("/policy/evaluate", json={
        "score_input": {
            "system_name": "NistFloor",
            "components": [
                # Weighted so composite ~85 (allow) but 'manage' by itself is 30.
                {"name": "strong_measure", "value": 1.0, "weight": 0.9,
                 "nist_function": "measure"},
                {"name": "weak_manage", "value": 0.3, "weight": 0.1,
                 "nist_function": "manage"},
            ],
        },
    })
    check("nist-floor 200", r.status_code == 200, r.text)
    body = r.json()
    # Composite = 1.0*0.9 + 0.3*0.1 = 0.93 -> 93 -> LOW tier.
    check("nist-floor composite ~93",
          abs(body["composite_score"] - 93.0) < 0.01,
          f"got {body['composite_score']}")
    check("nist-floor tier LOW", body["tier"] == "LOW")
    # Despite LOW tier, NIST manage = 30 < floor 40 -> overall block.
    check("nist-floor overall BLOCK",
          body["decision"] == "block",
          f"got {body['decision']}")
    reason_codes = [r["code"] for r in body["reasons"]]
    check("nist-floor has composite_meets_allow reason",
          "composite_meets_allow" in reason_codes)
    check("nist-floor has nist_manage_below_floor reason",
          "nist_manage_below_floor" in reason_codes,
          f"got {reason_codes}")
    # Block reasons come first (sorted by severity).
    check("nist-floor block reasons sorted first",
          body["reasons"][0]["severity"] == "block")

    # CUSTOM THRESHOLDS: stricter allow_min pushes a normally-allowed
    # score into the warn band.
    r = client.post("/policy/evaluate", json={
        "score_input": {
            "system_name": "Claims Triage Model",
            "components": [{"name": "x", "value": 0.85, "weight": 1.0}],
        },
        "thresholds": {
            "allow_min_composite": 90.0,
            "warn_min_composite": 60.0,
            "min_nist_function_score": 40.0,
        },
    })
    check("custom-threshold 200", r.status_code == 200)
    body = r.json()
    # 85 composite, allow threshold raised to 90 -> warn band.
    check("custom-threshold warn", body["decision"] == "warn")
    check("custom thresholds echoed",
          body["thresholds_applied"]["allow_min_composite"] == 90.0)

    # VALIDATION: warn_min_composite > allow_min_composite -> 422.
    r = client.post("/policy/evaluate", json={
        "score_input": {
            "system_name": "X",
            "components": [{"name": "x", "value": 0.5, "weight": 1.0}],
        },
        "thresholds": {
            "allow_min_composite": 70.0,
            "warn_min_composite": 80.0,
            "min_nist_function_score": 40.0,
        },
    })
    check("invalid thresholds -> 422", r.status_code == 422)

    # VALIDATION: empty components propagate to 422.
    r = client.post("/policy/evaluate", json={
        "score_input": {"system_name": "X", "components": []},
    })
    check("policy empty components -> 422", r.status_code == 422)

    # ---------- 16. Policy gate attached to /assessments (Sprint 3, E3-S2) ----------
    section("16. POST /assessments persists the policy gate decision (E3-S2)")

    # ALLOW: all four functions at 90 -> composite 90 -> LOW tier -> allow.
    r = client.post("/assessments", json={
        "system_name": "Policy Gated System - Strong",
        "owner": "Shannon Brian Kelly",
        "govern_score": 90, "map_score": 90,
        "measure_score": 90, "manage_score": 90,
    }, headers=hdr)
    check("strong assessment 201", r.status_code == 201, r.text)
    strong = r.json()
    check("strong overall = 90.0", abs(strong["overall_score"] - 90.0) < 1e-6)
    check("strong tier LOW", strong["risk_tier"] == "LOW")
    check("strong gate_decision allow",
          strong["gate_decision"] == "allow",
          f"got {strong['gate_decision']}")
    check("strong gate_reasons list",
          isinstance(strong["gate_reasons"], list))
    check("strong gate reasons each have code/message/severity",
          all({"code", "message", "severity"} <= set(reason.keys())
              for reason in strong["gate_reasons"]))
    check("strong gate reasons severities valid",
          all(reason["severity"] in {"info", "warn", "block"}
              for reason in strong["gate_reasons"]))
    # An 'allow' assessment has no block reasons.
    check("strong gate has no block reasons",
          all(reason["severity"] != "block"
              for reason in strong["gate_reasons"]))
    strong_id = strong["id"]

    # BLOCK (composite band): all four at 30 -> composite 30 -> HIGH -> block.
    r = client.post("/assessments", json={
        "system_name": "Policy Gated System - Weak",
        "owner": "Shannon Brian Kelly",
        "govern_score": 30, "map_score": 30,
        "measure_score": 30, "manage_score": 30,
    }, headers=hdr)
    check("weak assessment 201", r.status_code == 201, r.text)
    weak = r.json()
    check("weak overall = 30.0", abs(weak["overall_score"] - 30.0) < 1e-6)
    check("weak tier HIGH", weak["risk_tier"] == "HIGH")
    check("weak gate_decision block",
          weak["gate_decision"] == "block",
          f"got {weak['gate_decision']}")
    # Worst-severity first: the first reason must be a block.
    check("weak gate first reason is block severity",
          weak["gate_reasons"][0]["severity"] == "block")
    weak_codes = [reason["code"] for reason in weak["gate_reasons"]]
    check("weak gate has composite_below_warn code",
          "composite_below_warn" in weak_codes,
          f"got {weak_codes}")

    # NIST-FLOOR BLOCK: composite could be warn-band but one function floor
    # is violated -> overall block regardless of composite.
    # govern 20, others 95 -> overall = 0.25*20 + 0.25*95*3 = 76.25 (warn band)
    # but nist_govern = 20 < floor 40 -> block.
    r = client.post("/assessments", json={
        "system_name": "Policy Gated System - Governance Gap",
        "owner": "Shannon Brian Kelly",
        "govern_score": 20, "map_score": 95,
        "measure_score": 95, "manage_score": 95,
    }, headers=hdr)
    check("gov-gap assessment 201", r.status_code == 201, r.text)
    gap = r.json()
    check("gov-gap overall ~76.25",
          abs(gap["overall_score"] - 76.25) < 1e-6)
    check("gov-gap tier MEDIUM", gap["risk_tier"] == "MEDIUM")
    check("gov-gap gate_decision block (NIST floor trumps warn band)",
          gap["gate_decision"] == "block",
          f"got {gap['gate_decision']}")
    gap_codes = [reason["code"] for reason in gap["gate_reasons"]]
    check("gov-gap has nist_govern_below_floor reason",
          "nist_govern_below_floor" in gap_codes,
          f"got {gap_codes}")
    check("gov-gap also carries composite warn-band reason",
          "composite_below_allow" in gap_codes,
          f"got {gap_codes}")
    check("gov-gap first reason is block-severity",
          gap["gate_reasons"][0]["severity"] == "block")

    # GET /assessments (list) returns gate_decision on every row.
    r = client.get("/assessments", headers=hdr)
    check("list assessments 200", r.status_code == 200, r.text)
    all_rows = r.json()
    check("list has at least the 4 created rows",
          len(all_rows) >= 4, f"got {len(all_rows)}")
    check("every row exposes gate_decision key",
          all("gate_decision" in row for row in all_rows))
    check("every row exposes gate_reasons list",
          all(isinstance(row.get("gate_reasons"), list) for row in all_rows))
    # Every decision in the list must be one of the three allowed values.
    check("every gate_decision is allow|warn|block",
          all(row["gate_decision"] in {"allow", "warn", "block"}
              for row in all_rows))
    # Spot-check the strong row's decision stayed 'allow' after persistence.
    strong_in_list = next(row for row in all_rows if row["id"] == strong_id)
    check("persisted strong row still allow",
          strong_in_list["gate_decision"] == "allow")

    # GET /assessments/{id} returns gate_decision + gate_reasons too.
    r = client.get(f"/assessments/{strong_id}", headers=hdr)
    check("get single assessment 200", r.status_code == 200, r.text)
    single = r.json()
    check("single gate_decision preserved",
          single["gate_decision"] == "allow")
    check("single gate_reasons preserved",
          isinstance(single["gate_reasons"], list))
    check("single gate has no block reasons",
          all(reason["severity"] != "block"
              for reason in single["gate_reasons"]))

    # 404 path still works (and doesn't leak gate_decision from another row).
    r = client.get("/assessments/99999", headers=hdr)
    check("missing assessment -> 404", r.status_code == 404)

    # ---------- 17. Policy evaluation history + trends (Sprint 3, E3-S3) ----------
    section("17. GET /policy/history (audit log + trend stats)")

    # Empty system_name filter on a brand-new system returns count=0 cleanly.
    r = client.get("/policy/history?system_name=Fresh%20System")
    check("empty system history 200", r.status_code == 200, r.text)
    empty = r.json()
    check("empty history count=0", empty["stats"]["count"] == 0)
    check("empty history trend insufficient_data",
          empty["stats"]["trend_direction"] == "insufficient_data")
    check("empty history records []",
          empty["records"] == [])
    check("empty history system_name echoed",
          empty["system_name"] == "Fresh System")

    # Build a deterministic, chronological story for one system:
    # ALLOW (90) -> WARN (70) -> BLOCK (30) -> ALLOW (95) so we get
    # 3 decision transitions and a clear allow/warn/block distribution.
    history_system = "AuditLogSystem"
    history_inputs = [
        ("allow_v1", 0.90, "allow"),
        ("warn_v1", 0.70, "warn"),
        ("block_v1", 0.30, "block"),
        ("allow_v2", 0.95, "allow"),
    ]
    for name, value, _expected in history_inputs:
        r = client.post("/policy/evaluate", json={
            "score_input": {
                "system_name": history_system,
                "components": [
                    {"name": name, "value": value, "weight": 1.0},
                ],
            },
        })
        check(f"seed {name} 200", r.status_code == 200, r.text)
        seeded = r.json()
        check(f"seed {name} decision matches expected",
              seeded["decision"] == _expected,
              f"expected {_expected}, got {seeded['decision']}")

    # Pull the newly-seeded history back out.
    r = client.get(f"/policy/history?system_name={history_system}")
    check("audit log 200", r.status_code == 200, r.text)
    log = r.json()
    check("audit log count=4", log["stats"]["count"] == 4,
          f"got {log['stats']['count']}")
    check("audit log system_name filter echoed",
          log["system_name"] == history_system)
    check("audit log records length = 4", len(log["records"]) == 4)

    # Newest-first ordering: the last seeded call (95 -> allow) should be first.
    check("audit log newest-first decision == allow",
          log["records"][0]["decision"] == "allow")
    check("audit log newest-first composite == 95.0",
          abs(log["records"][0]["composite_score"] - 95.0) < 1e-6)

    # Every record carries the full gate payload we persisted.
    for row in log["records"]:
        check("row exposes id", isinstance(row["id"], int))
        check("row system_name matches filter",
              row["system_name"] == history_system)
        check("row decision is allow|warn|block",
              row["decision"] in {"allow", "warn", "block"})
        check("row reasons is list",
              isinstance(row["reasons"], list) and len(row["reasons"]) >= 1)
        check("row thresholds echoed",
              row["thresholds"]["allow_min_composite"] == 80.0)

    # Stats: latest / earliest decisions + composites.
    stats = log["stats"]
    check("stats latest_decision allow",
          stats["latest_decision"] == "allow")
    check("stats latest_composite 95.0",
          abs(stats["latest_composite"] - 95.0) < 1e-6)
    check("stats earliest_decision allow",
          stats["earliest_decision"] == "allow")
    check("stats earliest_composite 90.0",
          abs(stats["earliest_composite"] - 90.0) < 1e-6)

    # Per-decision counts: 2 allow, 1 warn, 1 block in our seed.
    check("stats allow_count=2", stats["allow_count"] == 2)
    check("stats warn_count=1", stats["warn_count"] == 1)
    check("stats block_count=1", stats["block_count"] == 1)
    check("stats allow_rate=0.5",
          abs(stats["allow_rate"] - 0.5) < 1e-6)
    check("stats warn_rate=0.25",
          abs(stats["warn_rate"] - 0.25) < 1e-6)
    check("stats block_rate=0.25",
          abs(stats["block_rate"] - 0.25) < 1e-6)

    # Composite min / max / rolling average across [90, 70, 30, 95].
    check("stats min_composite=30.0",
          abs(stats["min_composite"] - 30.0) < 1e-6)
    check("stats max_composite=95.0",
          abs(stats["max_composite"] - 95.0) < 1e-6)
    check("stats rolling_average_composite=71.25",
          abs(stats["rolling_average_composite"] - 71.25) < 1e-6,
          f"got {stats['rolling_average_composite']}")

    # trend_direction: older half mean = (90+70)/2 = 80, newer half mean
    # = (30+95)/2 = 62.5 -> delta -17.5 -> degrading.
    check("stats trend_direction=degrading",
          stats["trend_direction"] == "degrading",
          f"got {stats['trend_direction']}")

    # decision_transitions: allow->warn, warn->block, block->allow (3 total).
    transitions = stats["decision_transitions"]
    check("3 decision transitions", len(transitions) == 3,
          f"got {len(transitions)}")
    check("transition 1: allow->warn",
          transitions[0]["from_decision"] == "allow"
          and transitions[0]["to_decision"] == "warn")
    check("transition 2: warn->block",
          transitions[1]["from_decision"] == "warn"
          and transitions[1]["to_decision"] == "block")
    check("transition 3: block->allow",
          transitions[2]["from_decision"] == "block"
          and transitions[2]["to_decision"] == "allow")
    # Every transition echoes the composite at that moment.
    check("transition composites are floats",
          all(isinstance(t["composite_score"], (int, float))
              for t in transitions))

    # limit=2 cap returns the two newest rows only.
    r = client.get(f"/policy/history?system_name={history_system}&limit=2")
    check("audit log limit=2 200", r.status_code == 200)
    capped = r.json()
    check("capped records length=2", len(capped["records"]) == 2)
    check("capped stats count=2", capped["stats"]["count"] == 2)
    # Limited window is just [allow 95, block 30] -> only one transition.
    check("capped transitions len=1",
          len(capped["stats"]["decision_transitions"]) == 1)

    # Unfiltered history includes at least the 4 seeded rows.
    r = client.get("/policy/history?limit=100")
    check("audit log unfiltered 200", r.status_code == 200)
    all_log = r.json()
    check("unfiltered count >= 4",
          all_log["stats"]["count"] >= 4,
          f"got {all_log['stats']['count']}")
    check("unfiltered system_name is null",
          all_log["system_name"] is None)

    # Validation: limit outside [1, 500] rejected.
    r = client.get("/policy/history?limit=0")
    check("history limit=0 -> 422", r.status_code == 422)
    r = client.get("/policy/history?limit=501")
    check("history limit=501 -> 422", r.status_code == 422)

    # Validation: empty system_name rejected.
    r = client.get("/policy/history?system_name=")
    check("history empty system_name -> 422", r.status_code == 422)

    # ---------- 18. Release approvals (Sprint 5, E5-S1) ----------
    section("18. Release approval workflow with separated approvers (Sprint 5, E5-S1)")

    r = client.get("/release/approvals/current")
    check("release approvals current requires auth -> 401", r.status_code == 401)

    for email in (
        "security.lead@example.com",
        "compliance.lead@example.com",
        "security.self@example.com",
    ):
        r = client.post("/auth/register", json={
            "email": email,
            "password": "correcthorsebatterystaple",
        })
        check(f"register {email} 201", r.status_code == 201, r.text)

    set_role("security.lead@example.com", "security_lead")
    set_role("compliance.lead@example.com", "compliance_lead")
    set_role("security.self@example.com", "security_lead")

    r = client.post("/auth/login", json={
        "email": "security.lead@example.com",
        "password": "correcthorsebatterystaple",
    })
    check("security lead login 200", r.status_code == 200, r.text)
    security_hdr = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post("/auth/login", json={
        "email": "compliance.lead@example.com",
        "password": "correcthorsebatterystaple",
    })
    check("compliance lead login 200", r.status_code == 200, r.text)
    compliance_hdr = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post("/auth/login", json={
        "email": "security.self@example.com",
        "password": "correcthorsebatterystaple",
    })
    check("security self login 200", r.status_code == 200, r.text)
    self_security_hdr = {"Authorization": f"Bearer {r.json()['access_token']}"}

    r = client.post(
        "/release/approvals/request",
        headers=self_security_hdr,
        json={"request_notes": "Self-requested release candidate"},
    )
    check("self requester approval request 200", r.status_code == 200, r.text)
    self_summary = r.json()
    check("self requester creates 2 approval records",
          len(self_summary["approvals"]) == 2)
    self_security_id = next(
        row["id"] for row in self_summary["approvals"]
        if row["approval_type"] == "security_lead"
    )

    r = client.post(
        f"/release/approvals/{self_security_id}/approve",
        headers=self_security_hdr,
        json={"approval_notes": "Trying to self-approve"},
    )
    check("self approval blocked 403", r.status_code == 403, r.text)

    clear_release_approvals()

    r = client.post(
        "/release/approvals/request",
        headers=hdr,
        json={"request_notes": "Release candidate ready for review"},
    )
    check("user approval request 200", r.status_code == 200, r.text)
    approval_summary = r.json()
    check("release not ready before approvals",
          approval_summary["ready_for_release"] is False)
    check("2 release approvals created",
          len(approval_summary["approvals"]) == 2)
    check("2 approval types pending",
          len(approval_summary["pending_approval_types"]) == 2)
    security_id = next(
        row["id"] for row in approval_summary["approvals"]
        if row["approval_type"] == "security_lead"
    )
    compliance_id = next(
        row["id"] for row in approval_summary["approvals"]
        if row["approval_type"] == "compliance_lead"
    )

    r = client.post(
        f"/release/approvals/{security_id}/approve",
        headers=compliance_hdr,
        json={"approval_notes": "Wrong lane"},
    )
    check("wrong approver role blocked 403", r.status_code == 403, r.text)

    r = client.post(
        f"/release/approvals/{security_id}/approve",
        headers=security_hdr,
        json={"approval_notes": "Security review complete"},
    )
    check("security approval 200", r.status_code == 200, r.text)
    approved_security = r.json()
    check("security approval status approved",
          approved_security["status"] == "approved")
    check("security approval by correct user",
          approved_security["approved_by_email"] == "security.lead@example.com")

    r = client.post(
        f"/release/approvals/{security_id}/approve",
        headers=security_hdr,
        json={"approval_notes": "Duplicate"},
    )
    check("duplicate approval blocked 409", r.status_code == 409, r.text)

    r = client.get("/release/approvals/current", headers=hdr)
    check("release approvals current 200", r.status_code == 200, r.text)
    mid_summary = r.json()
    check("one approval still pending after first approval",
          len(mid_summary["pending_approval_types"]) == 1)

    r = client.post(
        f"/release/approvals/{compliance_id}/approve",
        headers=compliance_hdr,
        json={"approval_notes": "Compliance review complete"},
    )
    check("compliance approval 200", r.status_code == 200, r.text)
    approved_compliance = r.json()
    check("compliance approval status approved",
          approved_compliance["status"] == "approved")

    r = client.get("/release/approvals/current", headers=hdr)
    check("release approvals ready summary 200", r.status_code == 200, r.text)
    ready_summary = r.json()
    check("release ready after both approvals",
          ready_summary["ready_for_release"] is True)
    check("no approval types pending",
          ready_summary["pending_approval_types"] == [])

    # ---------- 19. Dashboard + executive reporting (Sprint 4 / Sprint 5 slice) ----------
    section("19. GET /dashboard/summary and /reports/executive-summary(.pdf)")

    r = client.get("/dashboard/summary")
    check("dashboard summary requires auth -> 401", r.status_code == 401)

    r = client.get("/dashboard/summary", headers=hdr)
    check("dashboard summary 200", r.status_code == 200, r.text)
    dash = r.json()
    check("dashboard viewer_role user", dash["viewer_role"] == "user")
    check("dashboard has metric cards", len(dash["metrics"]) >= 4)
    check("dashboard has epic rows", len(dash["epics"]) == 5)
    check("dashboard embeds score history", "score_history" in dash)
    check("dashboard embeds policy history", "policy_history" in dash)
    check("dashboard embeds assessment summary", "assessment_summary" in dash)
    check("dashboard recent assessments list present",
          isinstance(dash["recent_assessments"], list))
    check("dashboard completion percent in range",
          0.0 <= dash["epic_completion_percent"] <= 100.0)

    r = client.get("/reports/executive-summary")
    check("executive summary requires auth -> 401", r.status_code == 401)

    r = client.get("/reports/executive-summary", headers=hdr)
    check("executive summary 200", r.status_code == 200, r.text)
    report = r.json()
    check("executive summary includes dashboard",
          "dashboard" in report and "compliance" in report)
    check("executive summary carries current branch",
          report["branch"] == "sprint-3/policy-audit-log")
    check("compliance controls present",
          len(report["compliance"]["controls"]) >= 5)
    check("compliance has outstanding gaps",
          len(report["compliance"]["outstanding_gaps"]) >= 1)
    check("compliance overall_status partial",
          report["compliance"]["overall_status"] == "partial")
    check("ci security control present",
          any(c["control_id"] == "CTRL-02" for c in report["compliance"]["controls"]))

    r = client.get("/reports/executive-summary.pdf", headers=hdr)
    check(
        "executive summary pdf 200",
        r.status_code == 200,
        r.headers.get("content-type", ""),
    )
    check("executive summary pdf content-type application/pdf",
          r.headers["content-type"].startswith("application/pdf"))
    check("executive summary pdf disposition header",
          "attachment; filename=\"earp-executive-summary.pdf\""
          in r.headers.get("content-disposition", ""))
    check("executive summary pdf starts with %PDF",
          r.content.startswith(b"%PDF"))
    pdf = PdfReader(io.BytesIO(r.content))
    check("executive summary pdf has >= 1 page", len(pdf.pages) >= 1)
    pdf_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    check("executive pdf mentions platform name",
          "Enterprise AI Reliability Platform" in pdf_text)
    check("executive pdf mentions compliance bundle",
          "Compliance Evidence Bundle" in pdf_text or "Security and compliance controls" in pdf_text)

    # ---------- 20. Audit ledger history + verification (Sprint 5, E5-S2 local slice) ----------
    section("20. GET /audit/history and /audit/verify (append-only hash chain)")

    audit_system = "AuditChainSystem"
    for name, value in [
        ("allow_seed", 0.90),
        ("warn_seed", 0.70),
        ("block_seed", 0.30),
    ]:
        r = client.post("/policy/evaluate", json={
            "score_input": {
                "system_name": audit_system,
                "components": [{"name": name, "value": value, "weight": 1.0}],
            },
        })
        check(f"audit seed {name} 200", r.status_code == 200, r.text)

    r = client.get("/audit/history", headers=hdr)
    check("audit history regular user blocked 403", r.status_code == 403, r.text)

    r = client.get(
        f"/audit/history?entity_type=policy_evaluation&entity_key={audit_system}",
        headers=security_hdr,
    )
    check("audit history security lead 200", r.status_code == 200, r.text)
    audit_history = r.json()
    check("audit history filter echoed entity_type",
          audit_history["entity_type"] == "policy_evaluation")
    check("audit history filter echoed entity_key",
          audit_history["entity_key"] == audit_system)
    check("audit history count=3",
          audit_history["stats"]["count"] == 3,
          f"got {audit_history['stats']['count']}")
    check("audit history records length=3",
          len(audit_history["records"]) == 3)
    check("audit history newest-first block decision",
          audit_history["records"][0]["payload"]["decision"] == "block")
    check("audit history latest_hash present",
          isinstance(audit_history["stats"]["latest_hash"], str)
          and len(audit_history["stats"]["latest_hash"]) == 64)
    check("audit history rows expose record hash",
          all(len(row["record_hash"]) == 64 for row in audit_history["records"]))
    check("audit history rows expose previous hash key",
          all("previous_hash" in row for row in audit_history["records"]))

    r = client.get("/audit/verify", headers=compliance_hdr)
    check("audit verify compliance lead 200", r.status_code == 200, r.text)
    audit_verify = r.json()
    check("audit chain valid before tamper",
          audit_verify["chain_valid"] is True,
          str(audit_verify["issues"]))
    check("audit verify checked_records >= filtered count",
          audit_verify["checked_records"] >= audit_history["stats"]["count"])

    r = client.get("/compliance/retention/status", headers=hdr)
    check("retention status regular user blocked 403", r.status_code == 403, r.text)

    r = client.get("/compliance/retention/policy", headers=security_hdr)
    check("retention policy default 200", r.status_code == 200, r.text)
    default_policy = r.json()
    check("default retention is seven years",
          default_policy["retention_days"] == 2555)

    r = client.post(
        "/compliance/retention/policy",
        headers=compliance_hdr,
        json={"retention_days": 0, "notes": "Local validation review window"},
    )
    check("set retention policy 200", r.status_code == 200, r.text)
    policy = r.json()
    check("retention policy set to 0 days",
          policy["retention_days"] == 0)
    check("retention policy actor captured",
          policy["configured_by_email"] == "compliance.lead@example.com")

    r = client.post(
        "/compliance/legal-holds",
        headers=security_hdr,
        json={
            "entity_type": "policy_evaluation",
            "entity_key": audit_system,
            "reason": "Hold audit chain validation sample",
        },
    )
    check("create legal hold 200", r.status_code == 200, r.text)
    hold = r.json()
    check("legal hold active", hold["active"] is True)
    check("legal hold targets audit system",
          hold["entity_key"] == audit_system)

    r = client.post(
        "/compliance/legal-holds",
        headers=security_hdr,
        json={
            "entity_type": "policy_evaluation",
            "entity_key": audit_system,
            "reason": "Duplicate hold",
        },
    )
    check("duplicate legal hold blocked 409", r.status_code == 409, r.text)

    r = client.get("/compliance/retention/status", headers=compliance_hdr)
    check("retention status compliance lead 200", r.status_code == 200, r.text)
    retention = r.json()
    check("retention status uses configured policy",
          retention["retention_days"] == 0)
    check("retention status sees active legal hold",
          retention["active_legal_holds"] >= 1)
    check("retention status holds audit sample records",
          retention["held_record_count"] >= 3,
          str(retention["held_record_ids"]))
    check("retention status has eligible records",
          retention["eligible_record_count"] > 0)

    r = client.post(
        f"/compliance/legal-holds/{hold['id']}/release",
        headers=compliance_hdr,
        json={"release_notes": "Validation complete"},
    )
    check("release legal hold 200", r.status_code == 200, r.text)
    released = r.json()
    check("legal hold inactive after release", released["active"] is False)
    check("legal hold released by compliance lead",
          released["released_by_email"] == "compliance.lead@example.com")

    r = client.post(
        f"/compliance/legal-holds/{hold['id']}/release",
        headers=compliance_hdr,
        json={"release_notes": "Duplicate release"},
    )
    check("duplicate legal hold release blocked 409", r.status_code == 409, r.text)

    tamper_id = audit_history["records"][0]["id"]
    db = SessionLocal()
    try:
        blocked = False
        row = db.query(AuditLogRecord).filter_by(id=tamper_id).first()
        row.actor_email = "mutator@example.com"
        db.add(row)
        try:
            db.commit()
        except Exception:
            blocked = True
            db.rollback()
    finally:
        db.close()
    check("audit row update blocked by append-only trigger", blocked)

    force_tamper_audit_record(tamper_id)

    r = client.get("/audit/verify", headers=security_hdr)
    check("audit verify after tamper 200", r.status_code == 200, r.text)
    tampered_verify = r.json()
    check("audit chain invalid after tamper",
          tampered_verify["chain_valid"] is False,
          str(tampered_verify["issues"]))
    check("audit verify surfaces record_hash_mismatch",
          any(issue["issue"] == "record_hash_mismatch"
              for issue in tampered_verify["issues"]),
          str(tampered_verify["issues"]))

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
