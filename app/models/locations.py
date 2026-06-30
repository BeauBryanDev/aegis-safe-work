
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
 
from app.core.database import Base
 
SCHEMA = "aegis_safe_work"

"""
Aegis-Safe-Work | ORM Models — Cameras and Locations
Represents the physical installation context: work sites, camera units,
and their configuration. Enables per-camera threshold overrides and
spatial mapping of alerts to physical locations for the frontend dashboard.
"""

#  thinking big on industrial  Usage 
class CameraStatus(str, enum.Enum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    FAULT    = "fault"
 
 
class CameraPosition(str, enum.Enum):
    FIXED   = "fixed"     # stationary mount
    PTZ     = "ptz"       # pan-tilt-zoom
    MOBILE  = "mobile"    # handheld / vehicle-mounted
 
 
# Work Site 


class WorkSite(Base):
    """
    A physical work site or facility being monitored.
    One site may have multiple cameras deployed across different zones.
    """
    __tablename__  = "work_sites"
    __table_args__ = (
        UniqueConstraint("site_code", name="uq_work_sites_site_code"),
        {"schema": SCHEMA},
    )
 
    id: Mapped[int]           = mapped_column(BigInteger, primary_key=True, autoincrement=True)
 
    # Identification
    site_code: Mapped[str]    = mapped_column(String(32), nullable=False)
    name:      Mapped[str]    = mapped_column(String(128), nullable=False)
    description: Mapped[str]  = mapped_column(Text, nullable=True)
    address :  Mapped[str]  =  mapped_column( Text , nullable=False )
    # Physical location (optional — for geo-mapping on the dashboard)
    city:      Mapped[str]    = mapped_column(String(64), nullable=True)
    country:   Mapped[str]    = mapped_column(String(64), nullable=True)
    latitude:  Mapped[float]  = mapped_column(Float, nullable=True)
    longitude: Mapped[float]  = mapped_column(Float, nullable=True)
 
    # Operational state
    is_active: Mapped[bool]   = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
 
    # Relationships
    cameras: Mapped[list["Camera"]] = relationship(
        "Camera",
        back_populates="site",
        cascade="all, delete-orphan",
    )
 
    def __repr__(self) -> str:
        return f"<WorkSite id={self.id} code={self.site_code} name={self.name}>"
 
 
# Camera 
class Camera(Base):
    """
    A single camera unit deployed at a work site.
    camera_id is a string identifier (e.g. 'CAM_A01') used as the foreign
    key reference across the detection tables in detections.py.
    Per-camera threshold overrides allow tuning sensitivity per deployment
    context (e.g. a high-angle wide-angle camera may need a lower fall
    threshold than a close-range camera).
    """
    __tablename__  = "cameras"
    __table_args__ = (
        UniqueConstraint("camera_id", name="uq_cameras_camera_id"),
        Index("ix_cameras_site_id", "site_id"),
        Index("ix_cameras_status",  "status"),
        {"schema": SCHEMA},
    )
 
    id: Mapped[int]              = mapped_column(BigInteger, primary_key=True, autoincrement=True)
 
    # Identification — camera_id string is the FK used in detection tables
    camera_id:   Mapped[str]     = mapped_column(String(64), nullable=False)
    display_name: Mapped[str]    = mapped_column(String(128), nullable=False)
    description:  Mapped[str]    = mapped_column(Text, nullable=True)
 
    # Physical install context
    site_id:    Mapped[int]    = mapped_column(
        BigInteger,
        nullable=False,
    )
    zone:    Mapped[str]    = mapped_column(String(64), nullable=True)  

    position: Mapped[ CameraPosition] = mapped_column(
        Enum(CameraPosition, schema=SCHEMA),
        nullable=False,
        default=CameraPosition.FIXED,
    )
    height_meters: Mapped[float] = mapped_column(Float, nullable=True)   # mounting height
 
    # Operational state
    status:      Mapped[CameraStatus] = mapped_column(
        Enum(CameraStatus, schema=SCHEMA),
        nullable=False,
        default=CameraStatus.ACTIVE,
    )
    stream_url:  Mapped[str]     = mapped_column(String(512), nullable=True)
 
    # Per-camera threshold overrides (null = use global config value from Settings)
    fall_threshold_override:     Mapped[float] = mapped_column(Float, nullable=True)
    ppe_conf_threshold_override: Mapped[float] = mapped_column(Float, nullable=True)
 
    # Frame resolution (populated on first frame received)
    frame_width:  Mapped[int]    = mapped_column(Integer, nullable=True)
    frame_height: Mapped[int]    = mapped_column(Integer, nullable=True)
 
    # Timestamps
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_seen_at: Mapped[datetime]  = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime]    = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
 
    # Relationship back to site
    site: Mapped["WorkSite"] = relationship("WorkSite", back_populates="cameras")
 
    @property
    def effective_fall_threshold(self) -> float:
        """
        Returns the per-camera override if set, otherwise falls back to
        the global FALL_THRESHOLD from Settings. Used by fall_service.py.
        """
        from app.core.config import settings
        return self.fall_threshold_override or settings.FALL_THRESHOLD
 
    @property
    def effective_ppe_conf_threshold(self) -> float:
        from app.core.config import settings
        return self.ppe_conf_threshold_override or settings.PPE_CONF_THRESHOLD
 
    def __repr__(self) -> str:
        return (
            f"<Camera id={self.id} camera_id={self.camera_id} "
            f"status={self.status} site_id={self.site_id}>"
        )
        
        