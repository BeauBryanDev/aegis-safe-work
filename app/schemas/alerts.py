
from datetime import datetime
from enum import Enum
from typing import Optional
 
from pydantic import BaseModel, Field, ConfigDict
 
""" 
Covers PPE non-compliance alerts, fall alerts, and fire/smoke alerts
as unified alert payloads for the frontend dashboard.
"""

class AlertType(str, Enum):
    PPE_VIOLATION  = "ppe_violation"
    FALL_DETECTED  = "fall_detected"
    FIRE_DETECTED  = "fire_detected"
    SMOKE_DETECTED = "smoke_detected"
 
 
class AlertSeverity(str, Enum):
    LOW      = "low"      # partial PPE missing 
    MEDIUM   = "medium"   # multiple PPE items missing
    HIGH     = "high"     # fall detected or critical PPE (helmet) missing
    CRITICAL = "critical" # fire or smoke detected
 
 
# Base Alert Schema
class AlertBase(BaseModel):
    camera_id:   str       = Field(..., description="Camera identifier, e.g. CAM_A01")
    alert_type:  AlertType
    severity:    AlertSeverity
    track_id:    Optional[int]  = Field(None, description="Tracker ID of the person involved, if applicable")
    description: Optional[str] = Field(None, description="Human-readable summary of the alert")
 

# Create Alert

class AlertCreate(AlertBase):
    detected_at:  datetime
    suppressed:   bool = False
 
 
# Alert Response 
class AlertOut(AlertBase):
    model_config = ConfigDict(from_attributes=True)
 
    id:          int
    detected_at: datetime
    suppressed:  bool
 
    # Bounding box of the subject (normalized 0-1), present for person-related alerts
    bbox_x1: Optional[float] = None
    bbox_y1: Optional[float] = None
    bbox_x2: Optional[float] = None
    bbox_y2: Optional[float] = None
 
    # Confidence or probability score depending on alert type
    score: Optional[float] = Field(
        None,
        description="Fall probability (fall alerts) or detection confidence (PPE/fire/smoke)"
    )
 
 
# List Alert Response

class AlertListOut(BaseModel):
    total:  int
    page:   int
    size:   int
    items:  list[AlertOut]
 
 
# Alert Stats for Dashboard

class AlertStats(BaseModel):
    total_alerts:       int
    fall_alerts:        int
    ppe_alerts:         int
    fire_smoke_alerts:  int
    active_cameras:     int
    period_start:       datetime
    period_end:         datetime
 
 
