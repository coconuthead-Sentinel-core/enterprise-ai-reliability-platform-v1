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
    check("E2 done (Sprint 2 complete)", epics[1]["status"] == "done")
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
    check("E2 is done (Epic E2 shipped in Sprint 2)",
          next(e for e in epics if e["id"] == "E2")["status"] == "done")

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
