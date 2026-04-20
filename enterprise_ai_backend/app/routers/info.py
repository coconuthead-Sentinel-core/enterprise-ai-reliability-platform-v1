"""Info router: read-only endpoints describing the project backlog and sprints.

These endpoints exist so the frontend dashboard and CI jobs can display the
current epic / sprint status without reading `product_backlog/product_backlog.txt`
from disk. Values are static for now and will be sourced from a service layer
in a later sprint.
"""
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/info", tags=["system"])


class Epic(BaseModel):
    """A product backlog epic and its current delivery status."""

    id: str
    title: str
    status: str  # one of: "not_started" | "in_progress" | "done"
    sprint: int


_EPICS: List[Epic] = [
    Epic(
        id="E1",
        title="Evidence Ingestion and Normalization",
        status="in_progress",
        sprint=1,
    ),
    Epic(
        id="E2",
        title="Reliability Scoring Engine",
        status="done",
        sprint=2,
    ),
    Epic(
        id="E3",
        title="Policy Gate Evaluation",
        status="done",
        sprint=3,
    ),
    Epic(
        id="E4",
        title="Dashboard and Reporting",
        status="in_progress",
        sprint=4,
    ),
    Epic(
        id="E5",
        title="Security and Compliance",
        status="in_progress",
        sprint=5,
    ),
]


@router.get("/epics", response_model=List[Epic])
def list_epics() -> List[Epic]:
    """Return the product backlog epics and their status."""
    return _EPICS


class SprintSummary(BaseModel):
    """High-level roadmap status for the frontend."""

    current_sprint: int
    total_sprints: int
    release: str
    branch: str


@router.get("/sprint", response_model=SprintSummary)
def current_sprint() -> SprintSummary:
    """Return the current sprint summary."""
    return SprintSummary(
        current_sprint=4,
        total_sprints=5,
        release="v0.3.0",
        branch="sprint-3/policy-audit-log",
    )
