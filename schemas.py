from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    context: str = Field(
        default="",
        description="System or environment context, such as Kubernetes namespace, recent deployment, service type."
    )
    logs: str = Field(
        ...,
        description="Raw logs or error messages to analyze."
    )


class AnalyzeResult(BaseModel):
    summary: str
    severity: Literal["critical", "high", "medium", "low", "unknown"]
    facts: List[str]
    inferences: List[str]
    root_cause: Optional[str]
    confidence: Literal["high", "medium", "low"]
    validation_commands: List[str]
    fix_suggestions: List[str]
    risk_notes: List[str]
    need_more_info: List[str]


class DiagnosePodRequest(BaseModel):
    namespace: str = Field(..., description="Kubernetes namespace")
    pod_name: str = Field(..., description="Kubernetes pod name")
    context: str = Field(
        default="",
        description="Optional extra context, such as recent deployment or service name."
    )