import re
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional

# --- CONFIGURATION LIMITS ---
MAX_RAW_PAYLOAD_CHARS = 50000  # Safe boundary (~50KB / ~500 lines) to prevent DoS

class HardenedAlertIngestion(BaseModel):
    source: str = Field(..., max_length=50)
    title: str = Field(..., max_length=100)
    severity: str = Field(..., max_length=10)
    raw: str

    @field_validator('raw')
    @classmethod
    def validate_and_sanitize_raw_payload(cls, v: str) -> str:
        # 1. Defend against Downstream Resource Exhaustion (DoS)
        if len(v) > MAX_RAW_PAYLOAD_CHARS:
            print(f"[!] Warning: Payload exceeded limit ({len(v)} chars). Truncating safely.")
            v = v[:MAX_RAW_PAYLOAD_CHARS] + "\n... [TRUNCATED FOR SYSTEM STABILITY]"
        
        # 2. Neutralize malicious SQL or script tags injections
        # Strip out explicit database destructive commands or comment sequences
        v = re.sub(r'(?i)(DROP\s+TABLE|DELETE\s+FROM|UNION\s+SELECT|ALTER\s+TABLE)', '[REDACTED_COMMAND]', v)
        v = v.replace(";", " ")  # Break basic SQL command chaining
        v = re.sub(r'<script.*?>.*?</script>', '[STRIPPED_SCRIPT]', v, flags=re.IGNORECASE)
        
        return v

def parse_raw_firewall_telemetry(raw_text: str) -> Dict[str, Any]:
    """
    Strict Regex Parser to extract telemetry fields safely without executing strings.
    """
    structured_data = {
        "src_ip": None,
        "dst_ip": None,
        "protocol": "UNKNOWN",
        "action": "UNKNOWN"
    }
    
    # Strictly bind regex patterns to match standard security parameters safely
    src_match = re.search(r'SRC=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', raw_text)
    dst_match = re.search(r'DST=(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', raw_text)
    proto_match = re.search(r'PROTO=([A-Za-z]+)', raw_text)
    action_match = re.search(r'ACTION=([A-Za-z]+)', raw_text)
    
    if src_match: structured_data["src_ip"] = src_match.group(1)
    if dst_match: structured_data["dst_ip"] = dst_match.group(1)
    if proto_match: structured_data["protocol"] = proto_match.group(1).upper()
    if action_match: structured_data["action"] = action_match.group(1).upper()
    
    return structured_data

# --- RUNNING TEST SCENARIOS ---
if __name__ == "__main__":
    print("[*] Running Ingestion Guard Testing Script...")

    # Scenario 1: Malicious SQL Injection String Injected inside Log
    malicious_input = {
        "source": "external_fw",
        "title": "Brute Force Log Entry",
        "severity": "high",
        "raw": "SRC=192.168.1.50 DST=10.0.0.5 PROTO=TCP ACTION=BLOCK; DROP TABLE alerts; --"
    }

    print("\n--- Testing Malicious SQL Injection Vector ---")
    validated_alert = HardenedAlertIngestion(**malicious_input)
    print(f"Sanitized Raw Payload Result:\n -> {validated_alert.raw}")
    
    # Parse telemetry out of the sanitized field safely
    extracted_fields = parse_raw_firewall_telemetry(validated_alert.raw)
    print(f"Extracted Fields Dictionary:\n -> {extracted_fields}")

    # Scenario 2: Massive DoS Payload String Injected
    print("\n--- Testing Massive 2MB Resource Exhaustion Vector ---")
    massive_string = "2026-06-27 fw-core SRC=1.1.1.1 DST=2.2.2.2 PROTO=UDP ACTION=DENY\n" * 20000 # ~1.2MB text string
    
    dos_input = {
        "source": "firewall_dump",
        "title": "Massive Log Flood",
        "severity": "medium",
        "raw": massive_string
    }
    
    validated_dos_alert = HardenedAlertIngestion(**dos_input)
    print(f"Final Character Length Post-Guard: {len(validated_dos_alert.raw)} characters.")
    
