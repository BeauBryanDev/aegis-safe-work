
from datetime import datetime
from enum import Enum
from typing import Optional
 
from pydantic import BaseModel, Field, ConfigDict, model_validator

""" 
Covers PPE non-compliance alerts, fall alerts, and fire/smoke alerts
as unified alert payloads for the frontend dashboard.
"""
class PPEComplianceStatus(str, Enum):
    COMPLIANT     = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL       = "partial"
 
 
class FireSmokeClass(str, Enum):
    FIRE  = "fire"
    SMOKE = "smoke"
 
 
# Raw detections from the PPE YOLOv11s model
class RawDetectionBox(BaseModel):
    class_id:   int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    x1:         float = Field(..., description="Normalized 0-1 relative to frame width")
    y1:         float = Field(..., description="Normalized 0-1 relative to frame height")
    x2:         float
    y2:         float


class RawDetection(BaseModel):
    camera_id:   str
    track_id:    int
    frame_number: int
    detections:  list[RawDetectionBox]


# personalized PPE compliance status
class PersonCompliance(BaseModel):
    track_id: int
 
    # Person bounding box (normalized 0-1)
    x1:       float
    y1:       float
    x2:       float
    y2:       float
    conf:     float = Field(..., ge=0.0, le=1.0)
 
    # PPE presence flags
    has_helmet: bool = False
    has_vest:   bool = False
    has_gloves: bool = False
    has_boots:  bool = False
    has_goggles: bool = False
 
    # Derived compliance status
    compliance_status: PPEComplianceStatus = PPEComplianceStatus.NON_COMPLIANT
 
    # Missing items list for frontend display (e.g. ["helmet", "gloves"])
    missing_items: list[str] = Field(default_factory=list)
 
    @model_validator(mode="after")
    def compute_compliance(self) -> "PersonCompliance":
        
        mandatory = [self.has_helmet, self.has_vest, self.has_gloves, self.has_boots, self.has_goggles]
        present   = sum(mandatory)
        missing   = []
 
        if not self.has_helmet: missing.append("helmet")
        if not self.has_vest:   missing.append("vest")
        if not self.has_gloves: missing.append("gloves")
        if not self.has_boots:  missing.append("boots")
 
        self.missing_items = missing
 
        if present == 4:
            self.compliance_status = PPEComplianceStatus.COMPLIANT
        elif present == 0:
            self.compliance_status = PPEComplianceStatus.NON_COMPLIANT
        else:
            self.compliance_status = PPEComplianceStatus.PARTIAL
 
        return self
    
    
# Full frame PPE result

class PPEFrameResult(BaseModel):
    camera_id:    str
    frame_number: Optional[int]  = None
    processed_at: datetime
    inference_ms: float
 
    # Per-person compliance results after spatial assignment
    persons: list[PersonCompliance] = Field(default_factory=list)
 
    # Raw counts (before spatial assignment and overcounting caps)
    raw_person_count: int = 0
    raw_helmet_count: int = 0
    raw_vest_count:   int = 0
    raw_gloves_count: int = 0
    raw_boots_count:  int = 0
 
    @property
    def compliant_count(self) -> int:
        return sum(1 for p in self.persons if p.compliance_status == PPEComplianceStatus.COMPLIANT)
 
    @property
    def non_compliant_count(self) -> int:
        return sum(1 for p in self.persons if p.compliance_status != PPEComplianceStatus.COMPLIANT)
 
    @property
    def has_violations(self) -> bool:
        return self.non_compliant_count > 0
 
 

# DB write schema for PPE detection table

class PPEDetectionCreate(BaseModel):
    camera_id:         str
    captured_at:       datetime
    frame_number:      Optional[int]
    track_id:          int
    person_x1:         float
    person_y1:         float
    person_x2:         float
    person_y2:         float
    person_conf:       float
    has_helmet:        bool
    has_vest:          bool
    has_gloves:        bool
    has_boots:         bool
    compliance_status: PPEComplianceStatus
    raw_helmet_count:  int = 0
    raw_vest_count:    int = 0
    raw_gloves_count:  int = 0
    raw_boots_count:   int = 0
    raw_person_count:  int = 0
    inference_ms:      Optional[float] = None
 
 
 
# Rest Response Schema
class PPEDetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id:                int
    camera_id:         str
    captured_at:       datetime
    frame_number:      Optional[int]
    track_id:          int
    person_x1:         float
    person_y1:         float
    person_x2:         float
    person_y2:         float
    person_conf:       float
    has_helmet:        bool
    has_vest:          bool
    has_gloves:        bool
    has_boots:         bool
    has_goggles:       bool
    compliance_status: PPEComplianceStatus
    inference_ms:      Optional[float]
 
 
# Web Socket Push Payload Real time frame buffer
class PPEWebSocketOut(BaseModel):
    event:        str = "ppe_frame"
    camera_id:    str
    frame_number: Optional[int]
    processed_at: datetime
    inference_ms: float
    persons:      list[PersonCompliance]
    has_violations: bool
 
 
# Fire and Smoke Detection
class FireSmokeWebSocketIn(BaseModel):
    """
    Payload structure expected from the browser when ONNX.js detects
    fire or smoke client-side. The backend validates, persists, and
    broadcasts the alert to other connected clients.
    """
    camera_id:           str
    class_name:          FireSmokeClass
    confidence:          float = Field(..., ge=0.0, le=1.0)
    x1:                  float
    y1:                  float
    x2:                  float
    y2:                  float
    client_frame_number: Optional[int]   = None
    client_latency_ms:   Optional[float] = None
    detected_at:         datetime
 
 
# Fire and Smoke DB Wirte schema
class FireSmokeEventCreate(BaseModel):
    camera_id:           str
    class_name:          FireSmokeClass
    confidence:          float
    x1:                  float
    y1:                  float
    x2:                  float
    y2:                  float
    client_frame_number: Optional[int]   = None
    client_latency_ms:   Optional[float] = None
    detected_at:         datetime
 
 
# Fire Smoke REST Response

class FireSmokeEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id:                  int
    camera_id:           str
    class_name:          FireSmokeClass
    confidence:          float
    x1:                  float
    y1:                  float
    x2:                  float
    y2:                  float
    client_frame_number: Optional[int]
    client_latency_ms:   Optional[float]
    detected_at:         datetime
 

# Paged List Response

class PPEDetectionListOut(BaseModel):
    total: int
    page:  int
    size:  int
    items: list[PPEDetectionOut]
 

class FireSmokeEventListOut(BaseModel):
    total: int
    page:  int
    size:  int
    items: list[FireSmokeEventOut]
 