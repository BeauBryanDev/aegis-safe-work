from collections.abc import AsyncGenerator
from typing import Annotated
 
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
 
from app.core.database import AsyncSessionLocal

"""
app/core/dependencies.py
Aegis-Safe-Work | FastAPI Dependency Injection
Centralizes shared dependencies: DB session, ONNX inference sessions,
tracker instance, frame buffer manager.
"""

# Database session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Re-exported here for convenience so routers only need to import
    from app.core.dependencies, not app.core.database directly.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
 
 
DBSession = Annotated[AsyncSession, Depends(get_db)]
 
 
# # ONNX Runtime sessions — loaded once at startup, stored on app.state

def get_ppe_session(request: Request):
    """
    Returns the ONNX Runtime InferenceSession for the PPE YOLOv11s model.
    Loaded once in main.py lifespan and stored on app.state.ppe_session.
    """
    session = getattr(request.app.state, "ppe_session", None)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PPE detection model is not loaded.",
        )
    return session



def get_fall_session(request: Request):
    """
    Returns the ONNX Runtime InferenceSession for the Fall Detector
    (EfficientNet-Lite0 + Temporal Attention MLP) model.
    Loaded once in main.py lifespan and stored on app.state.fall_session.
    """
    session = getattr(request.app.state, "fall_session", None)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fall detection model is not loaded.",
        )
    return session
 
 
PPESession  = Annotated[object, Depends(get_ppe_session)]
FallSession = Annotated[object, Depends(get_fall_session)]
 
 
# # Tracker — loaded once at startup, stored on app.state

def get_tracker(request: Request):
    """
    Returns the shared PersonTracker instance.
    Stateful across requests/connections — holds active track IDs and
    their last-known positions. Stored on app.state.tracker.
    """
    tracker = getattr(request.app.state, "tracker", None)
    if tracker is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tracker is not initialized.",
        )
    return tracker
 
 
TrackerDep = Annotated[object, Depends(get_tracker)]
 
 
# Frame buffer — loaded once at startup, stored on app.state

def get_frame_buffer_manager(request: Request):
    """
    Returns the shared FrameBufferManager instance.
    Maintains a circular buffer of the last N_FRAMES per track_id,
    used as input to the fall detector. Stored on app.state.frame_buffer_manager.
    """
    manager = getattr(request.app.state, "frame_buffer_manager", None)
    if manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Frame buffer manager is not initialized.",
        )
    return manager
 
 
FrameBufferDep = Annotated[object, Depends(get_frame_buffer_manager)]
 