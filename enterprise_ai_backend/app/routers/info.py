"""Info router — read-only metadata about epics and sprint status."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/info", tags=["info"])

EPICS = [
    {
        "id": "E1",
        "title": "Evidence Ingestion and Normalization",
        "stories": ["E1-S1", "E1-S2", "E1-S3"],
    },
    {
        "id": "E2",
        "title": "Reliability Scoring Engine",
        "stories": ["E2-S1", "E2-S2", "E2-S3"],
    },
    {
        "id": "E3",
        "title": "Policy Gate Evaluation",
        "stories": ["E3-S1", "E3-S2", "E3-S3"],
    },
    {
        "id": "E4",
        "title": "Dashboard and Reporting",
        "stories": ["E4-S1", "E4-S2", "E4-S3"],
    },
    {
        "id": "E5",
        "title": "Security and Compliance",
        "stories": ["E5-S1", "E5-S2", "E5-S3"],
    },
]

SPRINT_STATUS = {
    "current_sprint": 2,
    "sprints": [
        {"sprint": 0, "status": "done", "summary": "Initial release package on GitHub"},
        {"sprint": 1, "status": "done", "summary": "Info endpoints + sprint plan"},
        {
            "sprint": 2,
            "status": "in_progress",
            "summary": "Reliability Scoring Engine (Epic E2)",
        },
        {"sprint": 3, "status": "planned", "summary": "Policy Gate Evaluation (Epic E3)"},
        {"sprint": 4, "status": "planned", "summary": "Dashboard and Reporting (Epic E4)"},
        {"sprint": 5, "status": "planned", "summary": "Security and Compliance (Epic E5)"},
    ],
}


@router.get("/epics")
async def get_epics() -> list[dict]:
    """Return the five product-backlog epics."""
    return EPICS


@router.get("/sprint")
async def get_sprint() -> dict:
    """Return current sprint status and roadmap."""
    return SPRINT_STATUS
