from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.rules import analyze_signals

app = FastAPI(
    title="SUNPOR Operator Assist",
    version="0.1.0",
    description="Lightweight rule-based suggestions for the operator assistant UI.",
)


class SignalSnapshot(BaseModel):
    wincc_tag: str
    signal_group: str | None = None
    value_scaled: float | None = None
    value_raw: float | None = None
    quality: str | None = None
    timestamp: str | None = None


class AnalyzeRequest(BaseModel):
    production_line_id: int | None = None
    production_run_id: int | None = None
    signals: list[SignalSnapshot] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    suggestions: list[dict[str, Any]]
    signal_count: int
    engine: str = "rule_v1"


@app.get("/health")
def health():
    return {"status": "ok", "service": "operator-assist"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    suggestions = analyze_signals(
        [signal.model_dump() for signal in request.signals],
        production_run_id=request.production_run_id,
        production_line_id=request.production_line_id,
    )
    return AnalyzeResponse(
        suggestions=suggestions,
        signal_count=len(request.signals),
    )
