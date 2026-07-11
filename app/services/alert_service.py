
from datetime import datetime, timezone
from typing import Optional
 
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.core.config import settings
from app.core.exceptions import AlertPersistenceError, RecordNotFoundError
from app.core.logging import get_logger
from app.models.detections import (
    FallEvent,
    FireSmokeEvent,
    PPEDetection,
    PPEComplianceStatus as OrmPPEComplianceStatus,
    FallPrediction as OrmFallPrediction,
    FireSmokeClass as OrmFireSmokeClass,
)
from app.schemas.alerts import AlertOut, AlertSeverity, AlertStats, AlertType
from app.schemas.falls import FallEventCreate, FallEventOut, FallEventListOut, FallInferenceResult
from app.schemas.ppes import (
    FireSmokeEventCreate,
    FireSmokeEventOut,
    FireSmokeEventListOut,
    PPEDetectionCreate,
    PPEDetectionListOut,
    PPEDetectionOut,
    PPEFrameResult,
)
 
logger = get_logger(__name__)
"""  
Handles writing detection events to PostgreSQL and building
unified alert payloads for the frontend WebSocket broadcast.
 
"""

async def persist_ppe_frame(
    db:     AsyncSession,
    result: PPEFrameResult,
) -> list[PPEDetection]:
    """
    Persist one PPEDetection row per confirmed person in a processed frame.
    Skips persons without a track_id (tentative tracks filtered upstream).
 
    Args:
    db     : async DB session from dependency injection
    result : PPEFrameResult from ppe_service.run()
 
    Returns:
    list[PPEDetection] — ORM objects added to the session
    """
    rows = []
    for person in result.persons:
        try:
            row = PPEDetection(
                camera_id         = result.camera_id,
                captured_at       = result.processed_at,
                frame_number      = result.frame_number,
                track_id          = person.track_id,
                person_x1         = person.x1,
                person_y1         = person.y1,
                person_x2         = person.x2,
                person_y2         = person.y2,
                person_conf       = person.conf,
                has_helmet        = person.has_helmet,
                has_vest          = person.has_vest,
                has_gloves        = person.has_gloves,
                has_boots         = person.has_boots,
                has_goggles       = person.has_goggles,
                compliance_status = OrmPPEComplianceStatus(person.compliance_status.value),
                raw_helmet_count  = result.raw_helmet_count,
                raw_vest_count    = result.raw_vest_count,
                raw_gloves_count  = result.raw_gloves_count,
                raw_boots_count   = result.raw_boots_count,
                raw_person_count  = result.raw_person_count,
                inference_ms      = result.inference_ms,
            )
            db.add(row)
            rows.append(row)
        except Exception as e:
            raise AlertPersistenceError(
                f"Failed to build PPEDetection for track {person.track_id}: {e}"
            ) from e
 
    logger.debug(
        "PPE detections persisted",
        extra={
            "camera_id":   result.camera_id,
            "frame":       result.frame_number,
            "rows":        len(rows),
            "violations":  result.non_compliant_count,
        },
    )
    return rows
 
# Fall persistence
 
async def persist_fall_event(
    db:          AsyncSession,
    result:      FallInferenceResult,
    suppressed:  bool = False,
) -> FallEvent:
    """
    Persist one FallEvent row for a fall inference window result.
    Persists ALL inference results (both FALL and NORMAL) when called,
    so the caller decides which results to persist based on business logic.
    Typically only FALL predictions are persisted to avoid high write volume.
 
    Args:
        db         : async DB session
        result     : FallInferenceResult from falls_service._run_one()
        suppressed : True if this fall was within the alert cooldown window
 
    Returns:
        FallEvent ORM object
    """
    try:
        row = FallEvent(
            camera_id      = result.camera_id,
            detected_at    = result.detected_at,
            track_id       = result.track_id,
            probability    = result.probability,
            prediction     = OrmFallPrediction(result.prediction.value),
            threshold_used = result.threshold_used,
            buffer_frames  = result.buffer_frames,
            person_x1      = result.person_x1,
            person_y1      = result.person_y1,
            person_x2      = result.person_x2,
            person_y2      = result.person_y2,
            suppressed     = suppressed,
            inference_ms   = result.inference_ms,
        )
        db.add(row)
        await db.flush()   # get row.id without committing the transaction
 
    except Exception as e:
        raise AlertPersistenceError(
            f"Failed to persist FallEvent for track {result.track_id}: {e}"
        ) from e
 
    logger.info(
        "Fall event persisted",
        extra={
            "id":          row.id,
            "track_id":    result.track_id,
            "camera_id":   result.camera_id,
            "probability": result.probability,
            "prediction":  result.prediction.value,
            "suppressed":  suppressed,
        },
    )
    return row
 
# Fire/smoke persistence
 
async def persist_fire_smoke_event(
    db:    AsyncSession,
    event: FireSmokeEventCreate,
) -> FireSmokeEvent:
    """
    Persist one FireSmokeEvent row from a client-side ONNX.js detection.
    Always persisted regardless of cooldown suppression (full audit log).
 
    Args:
        db    : async DB session
        event : FireSmokeEventCreate built by fire_smoke_util.build_fire_smoke_event()
 
    Returns:
        FireSmokeEvent ORM object
    """
    try:
        row = FireSmokeEvent(
            camera_id           = event.camera_id,
            detected_at         = event.detected_at,
            class_name          = OrmFireSmokeClass(event.class_name.value),
            confidence          = event.confidence,
            x1                  = event.x1,
            y1                  = event.y1,
            x2                  = event.x2,
            y2                  = event.y2,
            client_frame_number = event.client_frame_number,
            client_latency_ms   = event.client_latency_ms,
        )
        db.add(row)
        await db.flush()
 
    except Exception as e:
        raise AlertPersistenceError(
            f"Failed to persist FireSmokeEvent for camera {event.camera_id}: {e}"
        ) from e
 
    logger.warning(
        "Fire/smoke event persisted",
        extra={
            "id":         row.id,
            "camera_id":  event.camera_id,
            "class_name": event.class_name.value,
            "confidence": event.confidence,
        },
    )
    return row
 
 
# Unified alert queries — REST API
 
async def get_fall_events(
    db:        AsyncSession,
    camera_id: Optional[str] = None,
    page:      int = 1,
    size:      int = 50,
) -> FallEventListOut:
    """
    Paginated query of fall events, newest first.
    Optionally filtered by camera_id.
    """
    stmt = select(FallEvent).order_by(desc(FallEvent.detected_at))
    if camera_id:
        stmt = stmt.where(FallEvent.camera_id == camera_id)
 
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total      = (await db.execute(count_stmt)).scalar_one()
 
    stmt   = stmt.offset((page - 1) * size).limit(size)
    rows   = (await db.execute(stmt)).scalars().all()
    items  = [FallEventOut.model_validate(r) for r in rows]
 
    return FallEventListOut(total=total, page=page, size=size, items=items)
 
 
async def get_ppe_detections(
    db:        AsyncSession,
    camera_id: Optional[str] = None,
    track_id:  Optional[int] = None,
    page:      int = 1,
    size:      int = 50,
) -> PPEDetectionListOut:
    """
    Paginated query of PPE detections, newest first.
    Optionally filtered by camera_id and/or track_id.
    """
    stmt = select(PPEDetection).order_by(desc(PPEDetection.captured_at))
    if camera_id:
        stmt = stmt.where(PPEDetection.camera_id == camera_id)
    if track_id is not None:
        stmt = stmt.where(PPEDetection.track_id == track_id)
 
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total      = (await db.execute(count_stmt)).scalar_one()
 
    stmt   = stmt.offset((page - 1) * size).limit(size)
    rows   = (await db.execute(stmt)).scalars().all()
    items  = [PPEDetectionOut.model_validate(r) for r in rows]
 
    return PPEDetectionListOut(total=total, page=page, size=size, items=items)
 
 
async def get_fire_smoke_events(
    db:        AsyncSession,
    camera_id: Optional[str] = None,
    page:      int = 1,
    size:      int = 50,
) -> FireSmokeEventListOut:
    """
    Paginated query of fire/smoke events, newest first.
    """
    stmt = select(FireSmokeEvent).order_by(desc(FireSmokeEvent.detected_at))
    if camera_id:
        stmt = stmt.where(FireSmokeEvent.camera_id == camera_id)
 
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total      = (await db.execute(count_stmt)).scalar_one()
 
    stmt   = stmt.offset((page - 1) * size).limit(size)
    rows   = (await db.execute(stmt)).scalars().all()
    items  = [FireSmokeEventOut.model_validate(r) for r in rows]
 
    return FireSmokeEventListOut(total=total, page=page, size=size, items=items)
 
 
async def get_alert_by_id(
    db:       AsyncSession,
    alert_id: int,
) -> AlertOut:
    """
    Fetch a single alert by ID, searching across all three detection tables.
    Returns the first match found (fall > fire_smoke > ppe priority order).
    Raises RecordNotFoundError if not found in any table.
    """
    # Check fall events
    fall = await db.get(FallEvent, alert_id)
    if fall:
        return _fall_to_alert_out(fall)
 
    # Check fire/smoke events
    fs = await db.get(FireSmokeEvent, alert_id)
    if fs:
        return _fire_smoke_to_alert_out(fs)
 
    # Check PPE detections (non-compliant only surfaced as alerts)
    ppe = await db.get(PPEDetection, alert_id)
    if ppe and ppe.compliance_status != OrmPPEComplianceStatus.COMPLIANT:
        return _ppe_to_alert_out(ppe)
 
    raise RecordNotFoundError("Alert", alert_id)
 
 
async def get_alert_stats(
    db:           AsyncSession,
    period_start: datetime,
    period_end:   datetime,
    camera_id:    Optional[str] = None,
) -> AlertStats:
    """
    Aggregate alert counts for the dashboard summary widgets.
    """
    def _cam_filter(model, stmt):
        if camera_id:
            return stmt.where(model.camera_id == camera_id)
        return stmt
 
    fall_stmt = _cam_filter(
        FallEvent,
        select(func.count()).where(
            FallEvent.detected_at.between(period_start, period_end),
            FallEvent.prediction == OrmFallPrediction.FALL,
            FallEvent.suppressed == False,
        )
    )
    ppe_stmt = _cam_filter(
        PPEDetection,
        select(func.count()).where(
            PPEDetection.captured_at.between(period_start, period_end),
            PPEDetection.compliance_status != OrmPPEComplianceStatus.COMPLIANT,
        )
    )
    fs_stmt = _cam_filter(
        FireSmokeEvent,
        select(func.count()).where(
            FireSmokeEvent.detected_at.between(period_start, period_end),
        )
    )
 
    fall_count = (await db.execute(fall_stmt)).scalar_one()
    ppe_count  = (await db.execute(ppe_stmt)).scalar_one()
    fs_count   = (await db.execute(fs_stmt)).scalar_one()
 
    return AlertStats(
        total_alerts      = fall_count + ppe_count + fs_count,
        fall_alerts       = fall_count,
        ppe_alerts        = ppe_count,
        fire_smoke_alerts = fs_count,
        active_cameras    = 0,   # populated by health router from app.state
        period_start      = period_start,
        period_end        = period_end,
    )
 
 
# Private converters — ORM row -> AlertOut
 
def _fall_to_alert_out(row: FallEvent) -> AlertOut:
    return AlertOut(
        id           = row.id,
        camera_id    = row.camera_id,
        alert_type   = AlertType.FALL_DETECTED,
        severity     = AlertSeverity.HIGH,
        track_id     = row.track_id,
        description  = (
            f"Fall detected for worker {row.track_id} "
            f"(probability {row.probability:.2f})"
        ),
        detected_at  = row.detected_at,
        suppressed   = row.suppressed,
        bbox_x1      = row.person_x1,
        bbox_y1      = row.person_y1,
        bbox_x2      = row.person_x2,
        bbox_y2      = row.person_y2,
        score        = row.probability,
    )
 
 
def _fire_smoke_to_alert_out(row: FireSmokeEvent) -> AlertOut:
    alert_type = (
        AlertType.FIRE_DETECTED
        if row.class_name == OrmFireSmokeClass.FIRE
        else AlertType.SMOKE_DETECTED
    )
    severity = (
        AlertSeverity.CRITICAL
        if row.class_name == OrmFireSmokeClass.FIRE
        else AlertSeverity.HIGH
    )
    return AlertOut(
        id           = row.id,
        camera_id    = row.camera_id,
        alert_type   = alert_type,
        severity     = severity,
        track_id     = None,
        description  = (
            f"{row.class_name.value.upper()} detected on camera {row.camera_id} "
            f"(confidence {row.confidence:.2f})"
        ),
        detected_at  = row.detected_at,
        suppressed   = False,
        bbox_x1      = row.x1,
        bbox_y1      = row.y1,
        bbox_x2      = row.x2,
        bbox_y2      = row.y2,
        score        = row.confidence,
    )
 
 
def _ppe_to_alert_out(row: PPEDetection) -> AlertOut:
    severity = (
        AlertSeverity.HIGH
        if not row.has_helmet
        else AlertSeverity.MEDIUM
    )
    return AlertOut(
        id           = row.id,
        camera_id    = row.camera_id,
        alert_type   = AlertType.PPE_VIOLATION,
        severity     = severity,
        track_id     = row.track_id,
        description  = (
            f"PPE violation for worker {row.track_id} "
            f"(status: {row.compliance_status.value})"
        ),
        detected_at  = row.captured_at,
        suppressed   = False,
        bbox_x1      = row.person_x1,
        bbox_y1      = row.person_y1,
        bbox_x2      = row.person_x2,
        bbox_y2      = row.person_y2,
        score        = row.person_conf,
    )