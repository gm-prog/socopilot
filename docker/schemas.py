import re
from pydantic import BaseModel, Field, field_validator

MAX_RAW_PAYLOAD_CHARS = 50000

class AlertCreateSchema(BaseModel):
    source: str = Field(..., max_length=50)
    title: str = Field(..., max_length=100)
    severity: str = Field(..., max_length=10)
    raw: str

    @field_validator('raw')
    @classmethod
    def validate_and_sanitize_raw_payload(cls, v: str) -> str:
        # 1. Defend against DoS / Resource Exhaustion
        if len(v) > MAX_RAW_PAYLOAD_CHARS:
            v = v[:MAX_RAW_PAYLOAD_CHARS] + "\n... [TRUNCATED FOR SYSTEM STABILITY]"
        
        # 2. Defend against SQL Injection and XSS Script Injections
        v = re.sub(r'(?i)(DROP\s+TABLE|DELETE\s+FROM|UNION\s+SELECT|ALTER\s+TABLE)', '[REDACTED_COMMAND]', v)
        v = v.replace(";", " ")
        v = re.sub(r'<script.*?>.*?</script>', '[STRIPPED_SCRIPT]', v, flags=re.IGNORECASE)
        
        return v
