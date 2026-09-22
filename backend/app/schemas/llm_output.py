"""Pydantic schemas for strict validation of LLM outputs."""

from pydantic import BaseModel, Field, field_validator


class LLMAIInsightOutput(BaseModel):
    """Validated output schema for AI alert analysis and insights."""
    summary: str = Field(..., description="Brief summary of the security event")
    severity_assessment: str = Field(default="medium", description="Assessed severity level")
    threat_category: str = Field(default="unknown", description="Categorization of threat")
    recommended_actions: list[str] = Field(default_factory=list, description="Remediation steps")
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("severity_assessment")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical", "unknown"}
        v_clean = v.lower().strip()
        return v_clean if v_clean in allowed else "medium"
