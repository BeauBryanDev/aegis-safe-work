
import time
from datetime import datetime, timezone
 
import numpy as np
import onnxruntime as ort
 
from app.core.config import settings
from app.core.exceptions import InferenceError
from app.core.logging import get_logger
from app.schemas.falls import (
    FallInferenceResult,
    FallPredictionLabel,
    FrameAttentionWeight,
)
from app.services.frame_buffer import FrameBuffer, FrameBufferManager
 
logger = get_logger(__name__)
 
"""  
Runs EfficientNet-Lite0 + Temporal Attention MLP inference on 16-frame
person crops from the FrameBufferManager. Returns a FallInferenceResult
"""

class FallService:
    """
    Inference wrapper around the EfficientNet-Lite0 + Attention MLP ONNX model.
    Instantiated once at startup and stored on app.state.
 
    Args:
    session  : onnxruntime.InferenceSession — loaded by main.py lifespan
    buffer_manager  : FrameBufferManager from app.state.frame_buffer_manager
    """
 
    def __init__(
        self,
        session:        ort.InferenceSession,
        buffer_manager: FrameBufferManager,
    ):
        self._session        = session
        self._buffer_manager = buffer_manager
 
        # Resolve input/output names from the ONNX graph
        self._input_name  = session.get_inputs()[0].name
        self._output_name = session.get_outputs()[0].name
        # In-memory cooldown: track_id -> last fall alert datetime
        # Prevents repeated alerts for the same person remaining on the ground
        self._last_fall_alert: dict[int, datetime] = {}
 
        logger.info(
            "FallService initialized",
            extra={
                "input_name":    self._input_name,
                "output_name":   self._output_name,
                "providers":     session.get_providers(),
                "threshold":     settings.FALL_THRESHOLD,
                "n_frames":      settings.N_FRAMES,
                "cooldown_s":    settings.ALERT_COOLDOWN_SECONDS,
            },
        )

    # Push a new crop into the buffer for a track
 
    def push_crop(
        self,
        track_id:  int,
        frame_rgb: np.ndarray,
    ) -> None:
        """
        Push a letterboxed (224, 224, 3) uint8 RGB person crop into the
        frame buffer for track_id. Called once per frame per confirmed track.
 
        Args:
        track_id  : tracker-assigned person ID
        frame_rgb : (224, 224, 3) uint8 RGB — already letterboxed by
                        crop_and_letterbox() in inference_service.py
        """
        self._buffer_manager.push(track_id, frame_rgb)

    # Run inference on all ready buffers
 
    def run_ready(
        self,
        camera_id:   str,
        track_boxes: dict[int, list[float]],
    ) -> list[FallInferenceResult]:
        """
        Check all frame buffers and run fall inference on those that are
        ready (full + step reached). Returns one FallInferenceResult per
        track that was inferenced this call.
 
        Args:
            camera_id   : camera identifier string
            track_boxes : dict mapping track_id -> [x1, y1, x2, y2] normalized
                          person bbox at current frame (for result metadata)
 
        Returns:
            list[FallInferenceResult] — one per buffer that ran inference,
            empty list if no buffers were ready this frame
        """
        ready_buffers = self._buffer_manager.get_ready_buffers()
 
        if not ready_buffers:
            return []
 
        results = []
        for buf in ready_buffers:
            result = self._run_one(buf, camera_id, track_boxes)
            if result is not None:
                results.append(result)
 
        return results
 
    # Run inference on one buffer
    
    def _run_one(
        self,
        buf:         FrameBuffer,
        camera_id:   str,
        track_boxes: dict[int, list[float]],
    ) -> FallInferenceResult | None:
        """
        Run fall inference on a single FrameBuffer and return the result.
        Returns None if inference fails (logged, not raised, to keep the
        WebSocket pipeline alive for other tracks).
        """
        track_id = buf.track_id
        t0       = time.perf_counter()
 
        try:
            tensor = buf.get_tensor()          # (1, 16, 3, 224, 224) float32
        except Exception as e:
            logger.error(
                "Failed to build tensor from frame buffer",
                extra={"track_id": track_id, "error": str(e)},
            )
            return None
 
        try:
            # ONNX model has two outputs:
            #   outputs[0] : (1, 1) float32 — sigmoid probability
            #   outputs[1] : (1, 16) float32 — attention weights, sum == 1
            outputs = self._session.run(
                None,
                {self._input_name: tensor},
            )
            probability  = float(outputs[0][0][0])
            attn_raw     = outputs[1][0]           # (16,) float32
 
        except Exception as e:
            raise InferenceError("EfficientNet-Lite0 Fall", str(e)) from e
 
        inference_ms = (time.perf_counter() - t0) * 1000
 
        # Determine prediction label
        prediction = (
            FallPredictionLabel.FALL
            if probability >= settings.FALL_THRESHOLD
            else FallPredictionLabel.NORMAL
        )
 
        # Cooldown suppression check
        suppressed = self._is_suppressed(track_id, prediction)
        if prediction == FallPredictionLabel.FALL and not suppressed:
            self._register_fall(track_id)
 
        # Build attention weights from real ONNX output[1]
        attn_weights = self._build_attention_weights(buf, attn_raw)
 
        # Person bbox at current frame
        bbox = track_boxes.get(track_id)
 
        result = FallInferenceResult(
            track_id       = track_id,
            camera_id      = camera_id,
            probability    = round(probability, 6),
            prediction     = prediction,
            threshold_used = settings.FALL_THRESHOLD,
            buffer_frames  = buf.frame_count,
            attention_weights = attn_weights,
            inference_ms   = round(inference_ms, 2),
            detected_at    = datetime.now(timezone.utc),
            person_x1      = bbox[0] if bbox else None,
            person_y1      = bbox[1] if bbox else None,
            person_x2      = bbox[2] if bbox else None,
            person_y2      = bbox[3] if bbox else None,
        )
 
        log_extra = {
            "track_id":    track_id,
            "camera_id":   camera_id,
            "probability": round(probability, 4),
            "prediction":  prediction.value,
            "suppressed":  suppressed,
            "inference_ms": round(inference_ms, 2),
        }
 
        if prediction == FallPredictionLabel.FALL:
            if suppressed:
                logger.debug("Fall detected but suppressed (cooldown)", extra=log_extra)
            else:
                logger.warning("FALL DETECTED", extra=log_extra)
        else:
            logger.debug("Fall inference: NORMAL", extra=log_extra)
 
        return result
 
 
    # Cooldown suppression
 
    def _is_suppressed(
        self,
        track_id:   int,
        prediction: FallPredictionLabel,
    ) -> bool:
        """
        Returns True if this fall alert should be suppressed because
        a fall was already alerted for this track_id within the cooldown
        window (settings.ALERT_COOLDOWN_SECONDS).
        NORMAL predictions are never suppressed.
        """
        if prediction != FallPredictionLabel.FALL:
            return False
 
        last = self._last_fall_alert.get(track_id)
        if last is None:
            return False
 
        now     = datetime.now(timezone.utc)
        elapsed = (now - last).total_seconds()
        
        return elapsed < settings.ALERT_COOLDOWN_SECONDS
    
 
    def _register_fall(self, track_id: int) -> None:
        self._last_fall_alert[track_id] = datetime.now(timezone.utc)
        
 
    def clear_cooldowns(self) -> None:
        """Reset all fall alert cooldowns. Useful for testing."""
        self._last_fall_alert.clear()
        logger.info("Fall alert cooldowns cleared.")
 
    # Attention weights helper
 
    def _build_attention_weights(
        self,
        buf: FrameBuffer,
    ) -> list[FrameAttentionWeight]:
        """
        Build FrameAttentionWeight list for the result schema.
 
        The fall detector ONNX export currently outputs only the sigmoid
        probability (single output node). Attention weights are not a
        separate output in the exported graph.
 
        Uniform weights still allow the frontend to render the attention
        bar chart component without crashing; values will be 1/N_FRAMES each.
        """
        n       = settings.N_FRAMES
        uniform = 1.0 / n
 
        return [
            FrameAttentionWeight(
                frame_index  = i,
                source_frame = i,   # source frame mapping not tracked here
                weight       = uniform,
            )
            for i in range(n)
        ]
 
    # Status
 
    def status(self) -> dict:
        """Snapshot for /health endpoint."""
        return {
            "threshold":       settings.FALL_THRESHOLD,
            "n_frames":        settings.N_FRAMES,
            "buffer_step":     settings.FRAME_BUFFER_STEP,
            "active_buffers":  self._buffer_manager.active_track_count,
            "cooldown_tracks": len(self._last_fall_alert),
            "buffers":         self._buffer_manager.status(),
        }