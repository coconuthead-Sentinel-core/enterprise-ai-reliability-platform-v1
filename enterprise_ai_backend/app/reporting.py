"""Dashboard aggregation + executive reporting helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from . import database, schemas, services
from .routers import info


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _fmt_percent(value: float | None) -> str:
    if value is None:
        return "No data"
    return f"{value:.1f}%"


def _fmt_score(value: float | None) -> str:
    if value is None:
        return "No data"
    return f"{value:.1f}"


def _status_for_threshold(
    actual: float | None,
    *,
    good_min: float | None = None,
    good_max: float | None = None,
) -> str:
    if actual is None:
        return "empty"
    if good_min is not None and actual >= good_min:
        return "good"
    if good_max is not None and actual <= good_max:
        return "good"
    return "attention"


def _dashboard_epics() -> List[schemas.DashboardEpic]:
    return [
        schemas.DashboardEpic(
            id=epic.id,
            title=epic.title,
            status=epic.status,
            sprint=epic.sprint,
        )
        for epic in info.list_epics()
    ]


def _assessment_summary(db: Session) -> schemas.AssessmentSummaryOut:
    rows = db.query(database.Assessment).all()
    summary = schemas.AssessmentSummaryOut(total=len(rows))
    for row in rows:
        if row.risk_tier == "LOW":
            summary.low_risk += 1
        elif row.risk_tier == "MEDIUM":
            summary.medium_risk += 1
        elif row.risk_tier == "HIGH":
            summary.high_risk += 1

        if row.gate_decision == "allow":
            summary.allow_count += 1
        elif row.gate_decision == "warn":
            summary.warn_count += 1
        elif row.gate_decision == "block":
            summary.block_count += 1
    return summary


def build_dashboard_summary(
    db: Session,
    viewer_role: str,
) -> schemas.DashboardSummaryOut:
    epics = _dashboard_epics()
    sprint = info.current_sprint()
    score_history = services.reliability_score_history(db, limit=12)
    policy_history = services.policy_evaluation_history(db, limit=12)
    recent_assessments = services.list_assessments(db, limit=6)
    assessment_summary = _assessment_summary(db)

    done_count = sum(1 for epic in epics if epic.status == "done")
    epic_completion = round(done_count / len(epics) * 100.0, 1) if epics else 0.0

    policy_pass_rate = (
        policy_history.stats.allow_rate * 100.0
        if policy_history.stats.allow_rate is not None
        else None
    )
    policy_block_rate = (
        policy_history.stats.block_rate * 100.0
        if policy_history.stats.block_rate is not None
        else None
    )
    rolling_score = score_history.stats.rolling_average

    metrics = [
        schemas.DashboardMetric(
            key="release_gate_pass_rate",
            label="Release Gate Pass Rate",
            value=_fmt_percent(policy_pass_rate),
            target=">= 80.0%",
            status=_status_for_threshold(policy_pass_rate, good_min=80.0),
            detail=(
                f"{policy_history.stats.allow_count} allow / "
                f"{policy_history.stats.count} policy evaluations"
                if policy_history.stats.count
                else "No policy evaluations logged yet."
            ),
        ),
        schemas.DashboardMetric(
            key="safety_violation_rate",
            label="Safety Violation Rate",
            value=_fmt_percent(policy_block_rate),
            target="<= 1.0%",
            status=_status_for_threshold(policy_block_rate, good_max=1.0),
            detail=(
                f"{policy_history.stats.block_count} blocked decisions in the "
                f"current history window"
                if policy_history.stats.count
                else "No policy decisions logged yet."
            ),
        ),
        schemas.DashboardMetric(
            key="mean_composite_score",
            label="Mean Composite Score",
            value=_fmt_score(rolling_score),
            target=">= 80.0",
            status=_status_for_threshold(rolling_score, good_min=80.0),
            detail=(
                f"Trend: {score_history.stats.trend_direction}"
                if score_history.stats.count
                else "No reliability score history yet."
            ),
        ),
        schemas.DashboardMetric(
            key="high_risk_assessments",
            label="High-Risk Assessments",
            value=str(assessment_summary.high_risk),
            target="0",
            status="good" if assessment_summary.high_risk == 0 else "attention",
            detail=f"{assessment_summary.total} total assessments on file",
        ),
        schemas.DashboardMetric(
            key="epic_completion",
            label="Epic Completion",
            value=_fmt_percent(epic_completion),
            target="Sprint 4 in progress",
            status="good" if done_count >= 2 else "attention",
            detail=f"{done_count} of {len(epics)} epics marked done",
        ),
    ]

    return schemas.DashboardSummaryOut(
        generated_at=_utcnow(),
        viewer_role=viewer_role,
        release=sprint.release,
        branch=sprint.branch,
        current_sprint=sprint.current_sprint,
        total_sprints=sprint.total_sprints,
        epics=epics,
        epic_completion_percent=epic_completion,
        metrics=metrics,
        assessment_summary=assessment_summary,
        recent_assessments=[
            schemas.AssessmentOutput.model_validate(row) for row in recent_assessments
        ],
        score_history=score_history,
        policy_history=policy_history,
    )


def build_compliance_evidence_bundle(
    dashboard: schemas.DashboardSummaryOut,
) -> schemas.ComplianceEvidenceBundleOut:
    controls = [
        schemas.ComplianceControlOut(
            control_id="CTRL-01",
            title="Authentication and Role Boundary",
            status="partial",
            summary=(
                "bcrypt password hashing, JWT access tokens, authenticated "
                "routes, and separated Security Lead / Compliance Lead "
                "release approvals are implemented."
            ),
            evidence=[
                "enterprise_ai_backend/app/security.py",
                "enterprise_ai_backend/app/routers/auth.py",
                "enterprise_ai_backend/app/routers/assessments.py",
                "enterprise_ai_backend/app/routers/dashboard.py",
                "enterprise_ai_backend/app/routers/release.py",
                "enterprise_ai_backend/app/routers/reports.py",
            ],
            gaps=[
                "Role assignment is still provisioned locally; no admin UI or SSO sync exists yet.",
            ],
        ),
        schemas.ComplianceControlOut(
            control_id="CTRL-02",
            title="CI Security Scanning",
            status="implemented",
            summary=(
                "Security scanning is wired into GitHub Actions with dependency "
                "audit, secret scanning, and CodeQL."
            ),
            evidence=[
                ".github/workflows/security-scans.yml",
                "docs/go-no-go.md",
                "docs/release-evidence.md",
            ],
            gaps=[],
        ),
        schemas.ComplianceControlOut(
            control_id="CTRL-03",
            title="Audit Logging and Release Traceability",
            status="partial",
            summary=(
                "Policy evaluations and release approvals are written into an "
                "append-only, hash-chained audit ledger for review and "
                "tamper detection."
            ),
            evidence=[
                "enterprise_ai_backend/app/database.py",
                "enterprise_ai_backend/app/services.py",
                "enterprise_ai_backend/app/routers/audit.py",
                "enterprise_ai_backend/app/routers/policy.py",
                "enterprise_ai_backend/app/routers/release.py",
            ],
            gaps=[
                "External immutable storage is not configured yet; the current "
                "ledger is local append-only plus tamper-evident verification.",
            ],
        ),
        schemas.ComplianceControlOut(
            control_id="CTRL-04",
            title="Release Governance",
            status="partial",
            summary=(
                "Local validation, CI evidence, go/no-go gates, and release "
                "workflow wiring are complete."
            ),
            evidence=[
                "docs/SPRINT_PLAN.md",
                "docs/go-no-go.md",
                "docs/release-evidence.md",
                ".github/workflows/release.yml",
            ],
            gaps=[
                "Azure deployment and live smoke tests remain blocked on secrets.",
            ],
        ),
        schemas.ComplianceControlOut(
            control_id="CTRL-05",
            title="Retention and Legal Hold",
            status="partial",
            summary=(
                "Local retention policy configuration and legal-hold "
                "registration/release flows are implemented for audit records."
            ),
            evidence=[
                "security_and_compliance_plan/security_and_compliance_plan.txt",
                "ga_hardening_compliance_launch/ga_hardening_compliance_launch.txt",
                "enterprise_ai_backend/app/routers/compliance.py",
                "enterprise_ai_backend/app/services.py",
            ],
            gaps=[
                "Cloud lifecycle enforcement and scheduled retention jobs are not configured yet.",
            ],
        ),
    ]

    outstanding_gaps = [
        "Add Azure deployment secrets and complete live smoke tests.",
        "Move the audit ledger into externally immutable storage.",
        "Move retention enforcement into cloud lifecycle policy or a scheduled job.",
    ]
    if dashboard.assessment_summary.high_risk > 0:
        outstanding_gaps.insert(
            0,
            f"{dashboard.assessment_summary.high_risk} high-risk assessments still need remediation.",
        )

    return schemas.ComplianceEvidenceBundleOut(
        generated_at=_utcnow(),
        overall_status="partial",
        controls=controls,
        outstanding_gaps=outstanding_gaps,
        recommended_next_steps=[
            "Keep Sprint 4 dashboard/reporting work local until Azure credentials exist.",
            "Use the PDF export as the review artifact for release and HR-facing walkthroughs.",
            "Treat external immutable audit storage and cloud retention enforcement as the next security hardening slice.",
        ],
    )


def build_executive_summary(
    db: Session,
    viewer_role: str,
) -> schemas.ExecutiveSummaryOut:
    dashboard = build_dashboard_summary(db, viewer_role=viewer_role)
    compliance = build_compliance_evidence_bundle(dashboard)
    return schemas.ExecutiveSummaryOut(
        generated_at=_utcnow(),
        viewer_role=viewer_role,
        release=dashboard.release,
        branch=dashboard.branch,
        current_sprint=dashboard.current_sprint,
        total_sprints=dashboard.total_sprints,
        dashboard=dashboard,
        compliance=compliance,
    )


def render_executive_summary_pdf(summary: schemas.ExecutiveSummaryOut) -> bytes:
    """Render the executive summary as a PDF attachment."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal = styles["BodyText"]
    small = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )

    story = [
        Paragraph("Enterprise AI Reliability Platform", title_style),
        Paragraph("Executive Summary and Compliance Evidence Bundle", heading_style),
        Paragraph(
            (
                f"Generated {summary.generated_at.strftime('%Y-%m-%d %H:%M UTC')} | "
                f"Release {summary.release} | Branch {summary.branch} | "
                f"Sprint {summary.current_sprint}/{summary.total_sprints}"
            ),
            small,
        ),
        Spacer(1, 0.18 * inch),
    ]

    story.append(Paragraph("KPI snapshot", heading_style))
    metric_rows = [["Metric", "Value", "Target", "Status", "Detail"]]
    for metric in summary.dashboard.metrics:
        metric_rows.append(
            [metric.label, metric.value, metric.target or "-", metric.status, metric.detail]
        )
    metric_table = Table(metric_rows, colWidths=[1.55 * inch, 0.85 * inch, 0.95 * inch, 0.8 * inch, 2.45 * inch])
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.extend([metric_table, Spacer(1, 0.2 * inch)])

    story.append(Paragraph("Epic progress", heading_style))
    epic_rows = [["Epic", "Title", "Status", "Sprint"]]
    for epic in summary.dashboard.epics:
        epic_rows.append([epic.id, epic.title, epic.status, str(epic.sprint)])
    epic_table = Table(epic_rows, colWidths=[0.55 * inch, 3.5 * inch, 1.1 * inch, 0.65 * inch])
    epic_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dcfce7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.extend([epic_table, Spacer(1, 0.2 * inch)])

    story.append(Paragraph("Assessment overview", heading_style))
    assessment = summary.dashboard.assessment_summary
    story.append(
        Paragraph(
            (
                f"Total assessments: {assessment.total}. "
                f"Low risk: {assessment.low_risk}. "
                f"Medium risk: {assessment.medium_risk}. "
                f"High risk: {assessment.high_risk}. "
                f"Gate decisions - allow: {assessment.allow_count}, "
                f"warn: {assessment.warn_count}, block: {assessment.block_count}."
            ),
            normal,
        )
    )
    story.append(Spacer(1, 0.12 * inch))

    recent_rows = [["System", "Owner", "Overall", "Risk", "Gate"]]
    if summary.dashboard.recent_assessments:
        for row in summary.dashboard.recent_assessments:
            recent_rows.append(
                [
                    row.system_name,
                    row.owner,
                    f"{row.overall_score:.1f}",
                    row.risk_tier,
                    row.gate_decision.value if row.gate_decision is not None else "-",
                ]
            )
    else:
        recent_rows.append(["No assessments yet", "-", "-", "-", "-"])
    recent_table = Table(
        recent_rows,
        colWidths=[2.15 * inch, 1.75 * inch, 0.7 * inch, 0.65 * inch, 0.65 * inch],
    )
    recent_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fef3c7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    story.extend([recent_table, Spacer(1, 0.2 * inch)])

    story.append(Paragraph("Security and compliance controls", heading_style))
    control_rows = [["Control", "Status", "Summary"]]
    for control in summary.compliance.controls:
        control_rows.append([control.control_id, control.status, control.summary])
    control_table = Table(control_rows, colWidths=[0.85 * inch, 0.85 * inch, 4.95 * inch])
    control_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([control_table, Spacer(1, 0.15 * inch)])

    story.append(Paragraph("Outstanding gaps", heading_style))
    for gap in summary.compliance.outstanding_gaps:
        story.append(Paragraph(f"- {gap}", normal))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("Recommended next steps", heading_style))
    for step in summary.compliance.recommended_next_steps:
        story.append(Paragraph(f"- {step}", normal))

    doc.build(story)
    return buffer.getvalue()
