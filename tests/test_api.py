"""Tests for the FastAPI application endpoints (integration-style)."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from enterprise_ai_backend.app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.anyio
async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_get_epics(client):
    resp = await client.get("/info/epics")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 5
    assert data[0]["id"] == "E1"


@pytest.mark.anyio
async def test_get_sprint(client):
    resp = await client.get("/info/sprint")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_sprint" in data
    assert isinstance(data["sprints"], list)


@pytest.mark.anyio
async def test_post_reliability_score_pass(client):
    payload = {
        "total_prompts": 1000,
        "successful_tasks": 1000,
        "supported_claims": 980,
        "unsupported_claims": 0,
        "policy_violations": 0,
        "p95_latency_ms": 500.0,
        "total_inference_cost_usd": 50.0,
        "total_requests": 1000,
        "compliant_requests": 1000,
        "adversarial_tests_total": 200,
        "adversarial_tests_passed": 200,
        "required_artifacts": 10,
        "complete_artifacts": 10,
        "availability": 1.0,
    }
    resp = await client.post("/reliability/score", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["gate_result"] == "pass"
    assert data["reliability_index"] >= 0.85
    assert data["policy_score"] >= 0.85
    assert "nist_rmf" in data
    assert data["hard_constraint_violations"] == []


@pytest.mark.anyio
async def test_post_reliability_score_fail(client):
    payload = {
        "total_prompts": 100,
        "successful_tasks": 30,
        "supported_claims": 50,
        "unsupported_claims": 50,
        "policy_violations": 10,
        "p95_latency_ms": 5000.0,
        "total_inference_cost_usd": 200.0,
        "total_requests": 100,
        "compliant_requests": 40,
        "adversarial_tests_total": 50,
        "adversarial_tests_passed": 20,
        "required_artifacts": 10,
        "complete_artifacts": 3,
        "availability": 0.90,
    }
    resp = await client.post("/reliability/score", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["gate_result"] == "fail"
    assert len(data["hard_constraint_violations"]) > 0


@pytest.mark.anyio
async def test_post_reliability_score_validation_error(client):
    resp = await client.post("/reliability/score", json={})
    assert resp.status_code == 422
