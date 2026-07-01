
from datetime import datetime
from enum import Enum
from typing import Optional
 
from pydantic import BaseModel, Field, ConfigDict


class FallPredictionLabel(str, Enum):
    NORMAL = "normal"
    FALL   = "fall"
 
 
# Per-frame attention weight 
class FrameAttentionWeight(BaseModel):
    frame_index:  int   = Field(..., description="Index within the 16-frame buffer (0-15)")
    source_frame: int   = Field(..., description="Original video frame number from the camera stream")
    weight:       float = Field(..., ge=0.0, le=1.0, description="Normalized attention weight for this frame")
 

## Raw inference result

class FallInferenceResult(BaseModel):
    track_id:       int
    camera_id:      str
    probability:    float                        = Field(..., ge=0.0, le=1.0)
    prediction:     FallPredictionLabel
    threshold_used: float                        = Field(default=0.65)
    buffer_frames:  int                          = Field(default=16)
    attention_weights: list[FrameAttentionWeight] = Field(default_factory=list)
    inference_ms:   float
    detected_at:    datetime
 
    # Person bounding box at time of inference (normalized 0-1)
    person_x1: Optional[float] = None
    person_y1: Optional[float] = None
    person_x2: Optional[float] = None
    person_y2: Optional[float] = None


# DB Write Schema


class FallEventCreate(BaseModel):
    camera_id:      str
    track_id:       int
    probability:    float
    prediction:     FallPredictionLabel
    threshold_used: float   = 0.65
    buffer_frames:  int     = 16
    suppressed:     bool    = False
    inference_ms:   Optional[float] = None
    detected_at:    datetime
    person_x1:      Optional[float] = None
    person_y1:      Optional[float] = None
    person_x2:      Optional[float] = None
    person_y2:      Optional[float] = None
 
 
# Rest Response Schema

class FallEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
 
    id:             int
    camera_id:      str
    track_id:       int
    probability:    float
    prediction:     FallPredictionLabel
    threshold_used: float
    buffer_frames:  int
    suppressed:     bool
    inference_ms:   Optional[float]
    detected_at:    datetime
    person_x1:      Optional[float]
    person_y1:      Optional[float]
    person_x2:      Optional[float]
    person_y2:      Optional[float]


# Websocker Push Payload  -> Rela time fall alert to frontend side

class FallWebSocketOut(BaseModel):
    event:          str   = "fall_detected"
    camera_id:      str
    track_id:       int
    probability:    float
    threshold_used: float
    detected_at:    datetime
    attention_weights: list[FrameAttentionWeight] = Field(default_factory=list)
 
    # Bounding box for frontend overlay rendering
    person_x1: Optional[float] = None
    person_y1: Optional[float] = None
    person_x2: Optional[float] = None
    person_y2: Optional[float] = None
 
 
# Paged List Response

class FallEventListOut(BaseModel):
    total: int
    page:  int
    size:  int
    items: list[FallEventOut]
 
 
 