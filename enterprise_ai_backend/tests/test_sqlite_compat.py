import sqlite3
import shutil
import tempfile
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

from app.database import init_db


def test_init_db_migrates_legacy_sqlite_assessments_table():
    temp_dir = Path(tempfile.mkdtemp(prefix="earp-sqlite-compat-"))
    db_path = temp_dir / "legacy-enterprise-ai.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE assessments (
                id INTEGER PRIMARY KEY,
                system_name VARCHAR(200) NOT NULL,
                owner VARCHAR(200) NOT NULL,
                govern_score INTEGER NOT NULL,
                map_score INTEGER NOT NULL,
                measure_score INTEGER NOT NULL,
                manage_score INTEGER NOT NULL,
                overall_score FLOAT NOT NULL,
                risk_tier VARCHAR(20) NOT NULL,
                notes TEXT,
                created_at DATETIME NOT NULL
            );

            INSERT INTO assessments (
                id,
                system_name,
                owner,
                govern_score,
                map_score,
                measure_score,
                manage_score,
                overall_score,
                risk_tier,
                notes,
                created_at
            ) VALUES (
                1,
                'Legacy System',
                'Legacy Owner',
                80,
                80,
                80,
                80,
                80.0,
                'LOW',
                'legacy row',
                '2026-04-20T00:00:00Z'
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    legacy_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    try:
        init_db(bind=legacy_engine)

        inspector = inspect(legacy_engine)
        assessment_columns = {
            column["name"] for column in inspector.get_columns("assessments")
        }
        assert "gate_decision" in assessment_columns
        assert "gate_reasons_json" in assessment_columns
        assert inspector.has_table("policy_evaluation_records")

        with legacy_engine.connect() as db:
            row = db.execute(
                text(
                    """
                    SELECT system_name, gate_decision, gate_reasons_json
                    FROM assessments
                    WHERE id = 1
                    """
                )
            ).mappings().one()

        assert row["system_name"] == "Legacy System"
        assert row["gate_decision"] is None
        assert row["gate_reasons_json"] is None
    finally:
        legacy_engine.dispose()
        shutil.rmtree(temp_dir, ignore_errors=True)
