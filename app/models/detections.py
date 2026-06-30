
import enum
from datetime import datetime, timezone
 
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
 
from app.core.database import Base
 
SCHEMA = "aegis_safe_work"
 
""" 
Aegis-Safe-Work | ORM Models — Detection Events
Three tables, 1/ model pipeline:
    - ppe_detections  : per-frame PPE compliance results per person
    - fall_events     : fall detector results per track_id per inference window
    - fire_smoke_events: fire/smoke events reported from client-side ONNX.js
"""

class PPEComplianceStatus(str, enum.Enum):
    COMPLIANT     = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIAL       = "partial"       # some items present, some missing
 
 
class FallPrediction(str, enum.Enum):
    NORMAL = "normal"
    FALL   = "fall"
 
 
class FireSmokeClass(str, enum.Enum):
    FIRE  = "fire"
    SMOKE = "smoke"
 
 
# PPE Detections 

class PPEDetection(Base):
    """
    One row per person per processed frame.
    PPE items are stored as boolean columns (present/absent) per person,
    derived from spatial assignment of YOLOv11s class detections to person
    bounding boxes.
    """
    __tablename__  = "ppe_detections"
    __table_args__ = (
        Index("ix_ppe_detections_track_id",   "track_id"),
        Index("ix_ppe_detections_captured_at", "captured_at"),
        Index("ix_ppe_detections_camera_id",   "camera_id"),
        {"schema": SCHEMA},
    )
 
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
 
    # Frame and source context
    camera_id:   Mapped[str]      = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    frame_number: Mapped[int]     = mapped_column(Integer, nullable=True)
 
    # Person identity from tracker
    track_id: Mapped[int]         = mapped_column(Integer, nullable=False)
 
    # Person bounding box (normalized 0-1 relative to frame dimensions)
    person_x1: Mapped[float]   = mapped_column(Float, nullable=False)
    person_y1: Mapped[float]   = mapped_column(Float, nullable=False)
    person_x2: Mapped[float]  = mapped_column(Float, nullable=False)
    person_y2: Mapped[float]   = mapped_column(Float, nullable=False)
    person_conf: Mapped[float]  = mapped_column(Float, nullable=False)
 
    # PPE presence flags (True = item detected on this person)
    has_helmet: Mapped[bool]  = mapped_column(Boolean, nullable=False, default=False)
    has_vest:   Mapped[bool]  = mapped_column(Boolean, nullable=False, default=False)
    has_gloves: Mapped[bool]  = mapped_column(Boolean, nullable=False, default=False)
    has_boots:  Mapped[bool]   = mapped_column(Boolean, nullable=False, default=False)
 
    # Aggregate compliance status derived from the four PPE flags
    compliance_status: Mapped[PPEComplianceStatus] = mapped_column(
        Enum(PPEComplianceStatus, schema=SCHEMA),
        nullable=False,
    )
 
    # Raw detection counts before spatial assignment (for debugging/audit)
    raw_helmet_count:  Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_vest_count:    Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_gloves_count:  Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_boots_count:   Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_person_count:  Mapped[int] = mapped_column(Integer, nullable=False, default=0)
 
    # Inference latency
    inference_ms: Mapped[float]   = mapped_column(Float, nullable=True)
 
    def __repr__(self) -> str:
        return (
            f"<PPEDetection id={self.id} track={self.track_id} "
            f"status={self.compliance_status} cam={self.camera_id}>"
        )
 
 
 
#  Fall Events 


class FallEvent(Base):
    """
    One row per fall detector inference window per track_id.
    Only persisted when probability >= FALL_THRESHOLD (a fall is detected),
    or optionally for all windows if full audit logging is enabled.
    """
    __tablename__  = "fall_events"
    __table_args__ = (
        Index("ix_fall_events_track_id",   "track_id"),
        Index("ix_fall_events_detected_at", "detected_at"),
        Index("ix_fall_events_camera_id",   "camera_id"),
        Index("ix_fall_events_prediction",  "prediction"),
        {"schema": SCHEMA},
    )
 
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
 
    # Frame and source context
    camera_id:   Mapped[str]      = mapped_column(String(64), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
 
    # Person identity from tracker
    track_id: Mapped[int]         = mapped_column(Integer, nullable=False)
 
    # Fall detector output
    probability: Mapped[float]    = mapped_column(Float, nullable=False)
    prediction:  Mapped[FallPrediction] = mapped_column(
        Enum(FallPrediction, schema=SCHEMA),
        nullable=False,
    )
    threshold_used: Mapped[float] = mapped_column(Float, nullable=False, default=0.65)
 
    # Person bounding box at time of inference (normalized 0-1)
    person_x1: Mapped[float]      = mapped_column(Float, nullable=True)
    person_y1: Mapped[float]      = mapped_column(Float, nullable=True)
    person_x2: Mapped[float]      = mapped_column(Float, nullable=True)
    person_y2: Mapped[float]      = mapped_column(Float, nullable=True)
 
    # Number of frames in buffer at time of inference (should always be N_FRAMES=16)
    buffer_frames: Mapped[int]    = mapped_column(Integer, nullable=False, default=16)
 
    # Alert suppression — True if this fall was within the cooldown window
    # of a prior fall event for the same track_id (not re-alerted to frontend)
    suppressed: Mapped[bool]      = mapped_column(Boolean, nullable=False, default=False)
 
    # Inference latency
    inference_ms: Mapped[float]   = mapped_column(Float, nullable=True)
 
    def __repr__(self) -> str:
        return (
            f"<FallEvent id={self.id} track={self.track_id} "
            f"pred={self.prediction} prob={self.probability:.4f} cam={self.camera_id}>"
        )


#  Fire / Smoke Events 


class FireSmokeEvent(Base):
    """
    Fire and smoke detections reported from the client-side YOLOv8n ONNX.js
    inference running in the browser. The browser sends structured detection
    payloads to the backend via the WebSocket stream; these are persisted here
    for audit and alert history.
    """
    __tablename__  = "fire_smoke_events"
    __table_args__ = (
        Index("ix_fire_smoke_events_detected_at", "detected_at"),
        Index("ix_fire_smoke_events_camera_id",   "camera_id"),
        Index("ix_fire_smoke_events_class_name",  "class_name"),
        {"schema": SCHEMA},
    )
 
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
 
    # Frame and source context
    camera_id:   Mapped[str]      = mapped_column(String(64), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
 
    # Detection class from YOLOv8n
    class_name:  Mapped[FireSmokeClass] = mapped_column(
        Enum(FireSmokeClass, schema=SCHEMA),
        nullable=False,
    )
    confidence:  Mapped[float]    = mapped_column(Float, nullable=False)
 
    # Bounding box as reported by client (normalized 0-1)
    x1: Mapped[float]             = mapped_column(Float, nullable=False)
    y1: Mapped[float]             = mapped_column(Float, nullable=False)
    x2: Mapped[float]             = mapped_column(Float, nullable=False)
    y2: Mapped[float]             = mapped_column(Float, nullable=False)
 
    # Client-side metadata
    client_frame_number: Mapped[int]   = mapped_column(Integer, nullable=True)
    client_latency_ms:   Mapped[float] = mapped_column(Float, nullable=True)
 
    def __repr__(self) -> str:
        return (
            f"<FireSmokeEvent id={self.id} class={self.class_name} "
            f"conf={self.confidence:.3f} cam={self.camera_id}>"
        )
 
 
 