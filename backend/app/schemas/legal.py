"""Legal / agreement schemas."""

from __future__ import annotations

from pydantic import BaseModel


class AgreementResponse(BaseModel):
    """The combined agreement shown in the signup modal."""

    version: str
    checkbox_label: str
    content: str
