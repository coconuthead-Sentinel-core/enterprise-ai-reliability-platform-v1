"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-04-19
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "llm_model_versions",
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(128), nullable=False),
        sa.Column("model_name", sa.String(128), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("model_id"),
    )

    op.create_table(
        "prompt_set_versions",
        sa.Column("prompt_set_id", sa.String(), nullable=False),
        sa.Column("prompt_set_version", sa.String(64), nullable=False),
        sa.Column("benchmark_suite_id", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("prompt_set_id"),
    )

    op.create_table(
        "llm_evaluation_runs",
        sa.Column("evaluation_id", sa.String(), nullable=False),
        sa.Column("model_id", sa.String(), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("prompt_set_id", sa.String(), nullable=False),
        sa.Column("prompt_set_version", sa.String(64), nullable=False),
        sa.Column("total_prompts", sa.Integer(), nullable=False),
        sa.Column("successful_tasks", sa.Integer(), nullable=False),
        sa.Column("supported_claims", sa.Integer(), nullable=False),
        sa.Column("unsupported_claims", sa.Integer(), nullable=False),
        sa.Column("policy_violations", sa.Integer(), nullable=False),
        sa.Column("p95_latency_ms", sa.Integer(), nullable=False),
        sa.Column("total_inference_cost_usd", sa.Numeric(12, 4), nullable=False),
        sa.Column("prompt_robustness", sa.Numeric(5, 4), nullable=False, server_default="1.0"),
        sa.Column("availability", sa.Numeric(5, 4), nullable=False, server_default="1.0"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["model_id"], ["llm_model_versions.model_id"]),
        sa.ForeignKeyConstraint(["prompt_set_id"], ["prompt_set_versions.prompt_set_id"]),
        sa.PrimaryKeyConstraint("evaluation_id"),
    )

    op.create_table(
        "gate_decisions",
        sa.Column("decision_id", sa.String(), nullable=False),
        sa.Column("evaluation_id", sa.String(), nullable=False),
        sa.Column("policy_id", sa.String(128), nullable=False),
        sa.Column("policy_score", sa.Numeric(5, 4), nullable=False),
        sa.Column(
            "result",
            sa.Enum("pass", "conditional", "fail", name="gateresult"),
            nullable=False,
        ),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["evaluation_id"], ["llm_evaluation_runs.evaluation_id"]
        ),
        sa.PrimaryKeyConstraint("decision_id"),
    )


def downgrade() -> None:
    op.drop_table("gate_decisions")
    op.drop_table("llm_evaluation_runs")
    op.drop_table("prompt_set_versions")
    op.drop_table("llm_model_versions")
    op.execute("DROP TYPE IF EXISTS gateresult")
