"""Legal / agreement routes."""

from __future__ import annotations

from fastapi import APIRouter

from app.legal.content import CHECKBOX_LABEL, COMBINED_AGREEMENT, LEGAL_VERSION
from app.schemas.legal import AgreementResponse

router = APIRouter(prefix="/legal", tags=["legal"])


@router.get("/agreement", response_model=AgreementResponse, summary="Signup agreement")
def get_agreement() -> AgreementResponse:
    """Return the combined agreement (Acknowledgment + ToS + Privacy) and version."""

    return AgreementResponse(
        version=LEGAL_VERSION,
        checkbox_label=CHECKBOX_LABEL,
        content=COMBINED_AGREEMENT,
    )
