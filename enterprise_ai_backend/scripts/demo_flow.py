"""Run the HR demo flow against a live EARP API."""
from __future__ import annotations

import argparse
import json
import time

import httpx


def request(client: httpx.Client, method: str, path: str, **kwargs):
    response = client.request(method, path, **kwargs)
    if response.status_code == 400 and path == "/auth/register":
        return response
    response.raise_for_status()
    return response


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the real EARP demo workflow.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default=f"hr-review-{int(time.time())}@example.com")
    parser.add_argument("--password", default="correcthorsebatterystaple")
    args = parser.parse_args()

    summary = {"base_url": args.base_url, "email": args.email}
    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=30.0) as client:
        summary["health"] = request(client, "GET", "/health").json()
        register = request(
            client,
            "POST",
            "/auth/register",
            json={"email": args.email, "password": args.password},
        )
        summary["register_status"] = register.status_code
        token = request(
            client,
            "POST",
            "/auth/login",
            json={"email": args.email, "password": args.password},
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        reliability_inputs = [
            {"mtbf_hours": 1000, "mttr_hours": 4, "mission_time_hours": 720},
            {"mtbf_hours": 50000, "mttr_hours": 2, "mission_time_hours": 8760},
            {"mtbf_hours": 2000, "mttr_hours": 6, "mission_time_hours": 720},
            {"mtbf_hours": 500, "mttr_hours": 10, "mission_time_hours": 720},
            {"mtbf_hours": 1500, "mttr_hours": 5, "mission_time_hours": 720},
            {"mtbf_hours": 20, "mttr_hours": 2, "mission_time_hours": 100},
        ]
        summary["reliability"] = [
            request(client, "POST", "/reliability/compute", json=payload).json()
            for payload in reliability_inputs
        ]
        summary["assessment"] = request(
            client,
            "POST",
            "/assessments",
            headers=headers,
            json={
                "system_name": "Claims Triage Model",
                "owner": "HR Review Demo",
                "govern_score": 85,
                "map_score": 78,
                "measure_score": 72,
                "manage_score": 81,
                "notes": "Created by demo_flow.py through the live API.",
            },
        ).json()
        summary["anomaly"] = request(
            client,
            "GET",
            "/ai/anomaly-detect/from-history?contamination=0.2",
            headers=headers,
        ).json()

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
