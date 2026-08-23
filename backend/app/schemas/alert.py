from pydantic import BaseModel, Field

class IngestAlertPayload(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant identifier")
    alert_name: str
    severity: str

    class Config:
        from_attributes = True
