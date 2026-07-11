import time
from collections import deque
 
import numpy as np
 
from app.core.config import settings
from app.core.logging import get_logger
 
logger = get_logger(__name__)
 
"""  
Aegis-Safe-Work | Per-Track Frame Buffer Manager
Maintains a circular buffer of the last N_FRAMES letterboxed RGB frames
per tracked person (track_id). The fall detector reads from this buffer
every FRAME_BUFFER_STEP new frames to decide if a fall occurred.
When a track_id disappears from the tracker (person leaves scene),
its buffer is evicted after TRACKER_MAX_AGE frames of absence
"""
class FrameBuffer:
    """
    Circular buffer of letterboxed RGB frames for one tracked person.
 
    Args:
        track_id  : tracker-assigned integer ID for this person
        maxlen    : maximum number of frames to hold (default N_FRAMES=16)
        step      : number of new frames required before triggering inference
    """
 
    def __init__(
        self,
        track_id: int,
        maxlen: int  = settings.FRAME_BUFFER_SIZE,
        step:   int  = settings.FRAME_BUFFER_STEP,
    ):
        self.track_id         = track_id
        self.maxlen           = maxlen
        self.step             = step
        self._buffer: deque   = deque(maxlen=maxlen)
        self._new_since_infer = 0   # frames pushed since last inference call
        self._last_seen_ts    = time.monotonic()
        self._infer_count     = 0   # total number of inference calls on this track

    # Push a new frame to the buffer
 
    def push(self, frame_rgb: np.ndarray) -> None:
        """
        Add a new letterboxed RGB frame (224, 224, 3) uint8 to the buffer.
        Evicts the oldest frame automatically when full (deque maxlen).
 
        Args:
            frame_rgb : (224, 224, 3) uint8 RGB — already letterboxed
        """
        self._buffer.append(frame_rgb)
        self._new_since_infer += 1
        self._last_seen_ts     = time.monotonic()
 
    # Inference readiness check

    @property
    def is_ready(self) -> bool:
        """
        True when the buffer has N_FRAMES frames AND enough new frames
        have accumulated since the last inference call.
        Both conditions must hold to trigger fall inference.
        """
        return (
            len(self._buffer) == self.maxlen
            and self._new_since_infer >= self.step
        )
 
    @property
    def frame_count(self) -> int:
        return len(self._buffer)
 
    @property
    def is_full(self) -> bool:
        return len(self._buffer) == self.maxlen
 
 
    # Get tensor for ONNX inference
 
    def get_tensor(self) -> np.ndarray:
        """
        Build and return a (1, 16, 3, 224, 224) float32 tensor from the
        current buffer contents, ready for the fall detector ONNX model.
 
        Resets the new-frame counter after building the tensor.
 
        Returns:
            np.ndarray : (1, 16, 3, 224, 224) float32
        """
        from app.utils.letterboxing import build_fall_tensor
 
        frames = list(self._buffer)  # oldest -> newest, length == maxlen
        tensor = build_fall_tensor(frames)
        self._new_since_infer = 0
        self._infer_count    += 1
        return tensor
 
 
    # Staleness check
 
    def seconds_since_last_seen(self) -> float:
        return time.monotonic() - self._last_seen_ts
 
    def __repr__(self) -> str:
        return (
            f"<FrameBuffer track={self.track_id} "
            f"frames={self.frame_count}/{self.maxlen} "
            f"new={self._new_since_infer}/{self.step} "
            f"inferences={self._infer_count}>"
        )
 


class FrameBufferManager:
    """
    Central manager for all active FrameBuffer instances.
    One instance lives on app.state.frame_buffer_manager for the lifetime
    of the FastAPI application.

    """
 
    def __init__(
        self,
        maxlen:      int   = settings.FRAME_BUFFER_SIZE,
        step:        int   = settings.FRAME_BUFFER_STEP,
        max_age_s:   float = settings.TRACKER_MAX_AGE / 30.0,  # frames -> seconds at ~30 FPS
    ):
        self.maxlen    = maxlen
        self.step      = step
        self.max_age_s = max_age_s
        self._buffers: dict[int, FrameBuffer] = {}
 

    # Push a frame crop for a specific track_id
 
    def push(self, track_id: int, frame_rgb: np.ndarray) -> None:
        """
        Push a letterboxed RGB frame crop into the buffer for track_id.
        Creates a new buffer automatically if this track_id is new.
 
        Args:
            track_id  : integer tracker ID assigned by PersonTracker
            frame_rgb : (224, 224, 3) uint8 RGB — already letterboxed crop
        """
        if track_id not in self._buffers:
            
            self._buffers[track_id] = FrameBuffer(
                track_id = track_id,
                maxlen   = self.maxlen,
                step     = self.step,
            )
            logger.debug(
                "New frame buffer created",
                extra={"track_id": track_id},
            )
 
        self._buffers[track_id].push(frame_rgb)
 
    # Get buffers ready for fall inference
 
    def get_ready_buffers(self) -> list[FrameBuffer]:
        """
        Return all FrameBuffer instances that are ready for fall inference
        (full + enough new frames accumulated since last inference).
 
        Returns:
            list[FrameBuffer] — may be empty if no track is ready
        """
        return [buf for buf in self._buffers.values() if buf.is_ready]
    
 
    def get_buffer(self, track_id: int) -> FrameBuffer | None:
        
        return self._buffers.get(track_id)
 
    # Evict stale buffers
    
    def evict_stale(self) -> list[int]:
        """
        Remove buffers for track_ids that have not received a new frame
        within max_age_s seconds. Called periodically by the WebSocket
        stream handler to free memory for workers that have left the scene.
 
        Returns:
            list[int] — track_ids that were evicted
        """
        evicted = [
            tid for tid, buf in self._buffers.items()
            if buf.seconds_since_last_seen() > self.max_age_s
        ]
        for tid in evicted:
            
            del self._buffers[tid]
            
            logger.debug(
                "Frame buffer evicted (track lost)",
                extra={"track_id": tid},
            )
            
        return evicted
 
    # Diagnostics
 
    @property
    def active_track_count(self) -> int:
        
        return len(self._buffers)
 
    def status(self) -> list[dict]:
        """
        Return a snapshot of all active buffers for the /health endpoint.
        """
        return [
            {
                "track_id":    tid,
                "frames":      buf.frame_count,
                "capacity":    buf.maxlen,
                "is_ready":    buf.is_ready,
                "inferences":  buf._infer_count,
                "idle_s":      round(buf.seconds_since_last_seen(), 2),
            }
            for tid, buf in self._buffers.items()
        ]
 
    def __repr__(self) -> str:
        
        return (
            f"<FrameBufferManager active_tracks={self.active_track_count} "
            f"maxlen={self.maxlen} step={self.step}>"
        )
 
    def __str__(self) -> str:
        
        return (
            f"FrameBufferManager(active_tracks={self.active_track_count}, "
            f"maxlen={self.maxlen}, step={self.step})"
        )   