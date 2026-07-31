from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class OperatorSuggestionConfirmRequest(BaseModel):
    suggestion_id: str
    production_run_id: int
    action: Literal["confirm", "dismiss", "correct"] = "confirm"
    level_1: str | None = None
    level_2: str | None = None
    level_3: str | None = None
    comment: str | None = None


class OperatorSuggestionConfirmResponse(BaseModel):
    status: str
    event_id: int | None = None
    message: str


class AssistSignalSnapshot(BaseModel):
    wincc_tag: str
    signal_group: str | None = None
    value_scaled: float | None = None
    value_raw: float | None = None
    quality: str | None = None
    timestamp: datetime | None = None


class AssistAnalyzeRequest(BaseModel):
    production_line_id: int | None = None
    production_run_id: int | None = None
    signals: list[AssistSignalSnapshot] = Field(default_factory=list)


class AssistSuggestion(BaseModel):
    id: str
    title: str
    message: str
    severity: Literal["info", "warning", "critical"] = "warning"
    confidence: float | None = None
    suggested_event: dict[str, Any] = Field(default_factory=dict)
    source: str = "operator_assist"
