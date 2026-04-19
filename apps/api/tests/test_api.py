"""End-to-end API integration tests covering the full gate evaluation pipeline."""


def _register_model(client):
    return client.post("/v1/models/versions", json={
        "provider": "OpenAI", "model_name": "gpt-4o", "model_version": "2024-05-13"
    })


def _register_prompt_set(client):
    return client.post("/v1/prompt-sets", json={
        "prompt_set_version": "v1.0", "benchmark_suite_id": "mmlu-v1"
    })


# --- Model version tests ---

def test_register_model_version(client):
    res = _register_model(client)
    assert res.status_code == 201
    data = res.json()
    assert data["provider"] == "OpenAI"
    assert "model_id" in data
    assert "registered_at" in data


def test_get_model_version(client):
    model_id = _register_model(client).json()["model_id"]
    res = client.get(f"/v1/models/versions/{model_id}")
    assert res.status_code == 200
    assert res.json()["model_id"] == model_id


def test_get_model_version_not_found(client):
    res = client.get("/v1/models/versions/nonexistent")
    assert res.status_code == 404


# --- Prompt set tests ---

def test_register_prompt_set(client):
    res = _register_prompt_set(client)
    assert res.status_code == 201
    data = res.json()
    assert "prompt_set_id" in data


# --- Evaluation tests ---

def test_submit_evaluation(client):
    model_id = _register_model(client).json()["model_id"]
    prompt_set_id = _register_prompt_set(client).json()["prompt_set_id"]

    res = client.post("/v1/evaluations", json={
        "model_id": model_id,
        "model_version": "2024-05-13",
        "prompt_set_id": prompt_set_id,
        "prompt_set_version": "v1.0",
        "total_prompts": 100,
        "successful_tasks": 90,
        "supported_claims": 85,
        "unsupported_claims": 10,
        "policy_violations": 2,
        "p95_latency_ms": 1200,
        "total_inference_cost_usd": "12.5000",
    })
    assert res.status_code == 202
    assert "evaluation_id" in res.json()


def test_submit_evaluation_invalid_model(client):
    _register_prompt_set(client).json()["prompt_set_id"]
    res = client.post("/v1/evaluations", json={
        "model_id": "bad-id",
        "model_version": "v1",
        "prompt_set_id": "also-bad",
        "prompt_set_version": "v1",
        "total_prompts": 10,
        "successful_tasks": 5,
        "supported_claims": 5,
        "unsupported_claims": 5,
        "policy_violations": 0,
        "p95_latency_ms": 500,
        "total_inference_cost_usd": "1.0",
    })
    assert res.status_code == 400


# --- Gate evaluation tests ---

def _full_pipeline(client, total=100, successful=95, supported=90, unsupported=5,
                   violations=1, latency=800):
    model_id = _register_model(client).json()["model_id"]
    prompt_set_id = _register_prompt_set(client).json()["prompt_set_id"]
    eval_id = client.post("/v1/evaluations", json={
        "model_id": model_id,
        "model_version": "2024-05-13",
        "prompt_set_id": prompt_set_id,
        "prompt_set_version": "v1.0",
        "total_prompts": total,
        "successful_tasks": successful,
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "policy_violations": violations,
        "p95_latency_ms": latency,
        "total_inference_cost_usd": "10.0",
    }).json()["evaluation_id"]
    return eval_id


def test_gate_evaluation_pass(client):
    eval_id = _full_pipeline(client)
    res = client.post("/v1/gates/evaluate", json={
        "evaluation_id": eval_id, "policy_id": "default-v1"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["result"] == "pass"
    assert "decision_id" in data
    assert float(data["policy_score"]) >= 0.80


def test_gate_evaluation_missing_eval(client):
    res = client.post("/v1/gates/evaluate", json={
        "evaluation_id": "does-not-exist", "policy_id": "default-v1"
    })
    assert res.status_code == 422


# --- Audit report tests ---

def test_audit_report_roundtrip(client):
    eval_id = _full_pipeline(client)
    decision_id = client.post("/v1/gates/evaluate", json={
        "evaluation_id": eval_id, "policy_id": "default-v1"
    }).json()["decision_id"]

    res = client.get(f"/v1/reports/audit/{decision_id}")
    assert res.status_code == 200
    report = res.json()
    assert report["decision_id"] == decision_id
    assert report["evaluation_id"] == eval_id
    assert "model_id" in report
    assert "generated_at" in report


def test_audit_report_not_found(client):
    res = client.get("/v1/reports/audit/nonexistent")
    assert res.status_code == 404


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
