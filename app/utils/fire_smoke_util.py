from datetime import datetime, timezone
from typing import Optional
 
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.alerts import AlertSeverity
from app.schemas.ppes import FireSmokeClass, FireSmokeEventCreate, FireSmokeWebSocketIn
 
logger = get_logger(__name__)


def get_fire_smoke_severity(
    class_name: FireSmokeClass,
    confidence: float,
) -> AlertSeverity:
    """
    Determine alert severity from detection class and confidence score.
 
    Fire   -> always CRITICAL regardless of confidence
    Smoke  -> HIGH if confidence >= 0.70, MEDIUM otherwise
              (smoke at lower confidence may be steam, dust, or fog)
 
    Args:
        class_name : FireSmokeClass.FIRE or FireSmokeClass.SMOKE
        confidence : float in [0, 1] from ONNX.js client
 
    Returns:
        AlertSeverity
    """
    if class_name == FireSmokeClass.FIRE:
        return AlertSeverity.CRITICAL
 
    # Smoke
    if confidence >= 0.70:
        return AlertSeverity.HIGH
    
    return AlertSeverity.MEDIUM
 
 
_last_alert_times: dict[tuple[str, str], datetime] = {}
 
 
def is_suppressed(
    camera_id:  str,
    class_name: FireSmokeClass,
    cooldown_s: int | None = None,
) -> bool:
    """
    Check whether a fire/smoke alert for this camera+class combination
    is within the cooldown window and should be suppressed.
 
    Args:
        camera_id  : camera identifier string
        class_name : FireSmokeClass.FIRE or FireSmokeClass.SMOKE
        cooldown_s : cooldown window in seconds
                     (default settings.ALERT_COOLDOWN_SECONDS = 10)
 
    Returns:
        True if the alert should be suppressed, False if it should fire
    """
    cooldown = cooldown_s or settings.ALERT_COOLDOWN_SECONDS
    key      = (camera_id, class_name.value)
    now      = datetime.now(timezone.utc)
    last     = _last_alert_times.get(key)
 
    if last is None:
        return False
 
    elapsed = (now - last).total_seconds()
    
    return elapsed < cooldown
 
 

def register_alert(camera_id: str, class_name: FireSmokeClass) -> None:
    """
    Record the current timestamp for this camera+class alert.
    Call this immediately after a non-suppressed alert is emitted.
    """
    key = (camera_id, class_name.value)
    _last_alert_times[key] = datetime.now(timezone.utc)
 
 

def clear_cooldowns() -> None:
    """
    Reset all cooldown state. Useful for testing or manual reset
    via an admin endpoint without restarting the server.
    """
    _last_alert_times.clear()
    logger.info("Fire/smoke alert cooldown state cleared.")
 
 

def build_fire_smoke_event(
    payload: FireSmokeWebSocketIn,
) -> FireSmokeEventCreate:
    """
    Convert the validated incoming WebSocket payload into the schema
    used by alert_service.py to write to the fire_smoke_events table.
 
    Args:
        payload : FireSmokeWebSocketIn — validated Pydantic model from WebSocket
 
    Returns:
        FireSmokeEventCreate — ready for DB persistence
    """
    return FireSmokeEventCreate(
        camera_id           = payload.camera_id,
        class_name          = payload.class_name,
        confidence          = payload.confidence,
        x1                  = payload.x1,
        y1                  = payload.y1,
        x2                  = payload.x2,
        y2                  = payload.y2,
        client_frame_number = payload.client_frame_number,
        client_latency_ms   = payload.client_latency_ms,
        detected_at         = payload.detected_at,
    )
 
 
# Main Entry Point — called from stream websocket handler

def process_fire_smoke_payload(
    payload: FireSmokeWebSocketIn,
    cooldown_s: Optional[int] = None,
) -> dict:
    """
    Full processing pipeline for an incoming fire/smoke detection from
    the browser ONNX.js client.
 
    Steps:
    1. Determine alert severity
    2. Check cooldown suppression
    3. Build DB event object
    4. Register alert timestamp if not suppressed
    5. Return result dict for the WebSocket handler to act on
 
    Args:
        payload    : validated FireSmokeWebSocketIn from the WebSocket endpoint
        cooldown_s : optional cooldown override in seconds
 
    Returns:
        dict with keys:
            suppressed      : bool
            severity        : AlertSeverity
            event_create    : FireSmokeEventCreate (always — persisted regardless)
            description     : str — human-readable alert description for the frontend
    """
    
    severity   = get_fire_smoke_severity(payload.class_name, payload.confidence)
    suppressed = is_suppressed(payload.camera_id, payload.class_name, cooldown_s)
    event      = build_fire_smoke_event(payload)
 
    description = (
        f"{payload.class_name.value.upper()} detected on camera {payload.camera_id} "
        f"(confidence: {payload.confidence:.2f})"
    )
 
    if not suppressed:
        register_alert(payload.camera_id, payload.class_name)
        logger.warning(
            "Fire/smoke alert triggered",
            extra={
                "camera_id":  payload.camera_id,
                "class_name": payload.class_name.value,
                "confidence": payload.confidence,
                "severity":   severity.value,
            },
        )
    else:
        logger.debug(
            "Fire/smoke alert suppressed (cooldown active)",
            extra={
                "camera_id":  payload.camera_id,
                "class_name": payload.class_name.value,
            },
        )
 
    return {
        "suppressed":   suppressed,
        "severity":     severity,
        "event_create": event,
        "description":  description,
    }
 
 
 