"""POST /hash/sha256 - real SHA-256."""
from fastapi import APIRouter, HTTPException

from .. import services
from ..schemas import HashInput, HashOutput

router = APIRouter(prefix="/hash", tags=["utility"])


@router.post("/sha256", response_model=HashOutput)
def sha256_endpoint(payload: HashInput):
    if not payload.text:
        raise HTTPException(status_code=400, detail="text must not be empty")
    return HashOutput(
        text=payload.text,
        sha256=services.sha256_of(payload.text),
        length=len(payload.text),
    )
