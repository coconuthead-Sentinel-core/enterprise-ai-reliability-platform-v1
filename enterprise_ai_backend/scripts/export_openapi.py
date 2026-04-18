"""Export the FastAPI OpenAPI document to libs/schemas/openapi.json."""
from __future__ import annotations

import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import app


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    output = repo_root / "libs" / "schemas" / "openapi.json"
    output.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
