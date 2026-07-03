import time
from datetime import datetime, timezone
 
import numpy as np
import onnxruntime as ort
 
from app.core.config import settings
from app.core.exceptions import InferenceError, InvalidFrameError
from app.core.logging import get_logger
from app.schemas.ppes import (
    PPEFrameResult,
    RawDetectionBox,
)
from app.services.tracker import PersonTracker
from app.utils.preprocess import decode_yolo_output, preprocess_frame_ppe
from app.utils.spatial_assign import assign_ppe_to_persons, split_detections
 
logger = get_logger(__name__)

"""  
Runs YOLOv11s inference on a full video frame, decodes the raw ONNX output,
applies spatial assignment of PPE items to person bounding boxes, and
returns a PPEFrameResult with per-person compliance status.
"""

class PPEService:
    """
    Stateless inference wrapper around the YOLOv11s ONNX model.
    Instantiated once at startup and stored on app.state.
 
    Args:
        session : onnxruntime.InferenceSession — loaded by main.py lifespan
        tracker : PersonTracker instance from app.state.tracker
    """
 
    def __init__(
        self,
        session: ort.InferenceSession,
        tracker: PersonTracker,
    ):
        self._session     = session
        self._tracker     = tracker
        self._input_name  = session.get_inputs()[0].name
        self._output_name = session.get_outputs()[0].name
 
        logger.info(
            "PPEService initialized",
            extra={
                "input_name":  self._input_name,
                "output_name": self._output_name,
                "providers":   session.get_providers(),
            },
        )
 
    # Main inference method
 
    def run(
        self,
        frame_bgr:    np.ndarray,
        camera_id:    str,
        frame_number: int | None = None,
    ) -> PPEFrameResult:
        """
        Run full PPE detection pipeline on one BGR video frame.
 
        Args:
            frame_bgr    : (H, W, 3) uint8 BGR frame from the video stream
            camera_id    : camera identifier string
            frame_number : optional frame counter for logging and DB
 
        Returns:
            PPEFrameResult with per-person compliance status and raw counts
        """
        if frame_bgr is None or frame_bgr.size == 0:
            raise InvalidFrameError("Frame is None or empty.")
 
        orig_shape = frame_bgr.shape[:2]   # (H, W)
        t0         = time.perf_counter()
 
        #  Preprocess
        try:
            tensor, scale, pad = preprocess_frame_ppe(frame_bgr)
        except Exception as e:
            raise InvalidFrameError(f"Preprocessing failed: {e}") from e
 
        #  ONNX Runtime inference
        try:
            raw_output = self._session.run(
                [self._output_name],
                {self._input_name: tensor},
            )[0]                           # (1, 15, 8400)
        except Exception as e:
            raise InferenceError("YOLOv11s PPE", str(e)) from e
 
        # Decode YOLO output -> RawDetectionBox list
        detections_raw = decode_yolo_output(
            output      = raw_output,
            scale       = scale,
            pad         = pad,
            orig_shape  = orig_shape,
            conf_threshold = settings.PPE_CONF_THRESHOLD,
            iou_threshold  = settings.PPE_IOU_THRESHOLD,
        )
 
        raw_boxes = [RawDetectionBox(**d) for d in detections_raw]
 
        # Split person boxes from PPE item boxes
        person_boxes, ppe_boxes = split_detections(raw_boxes)

        # Update tracker with confirmed person boxes

        person_coords = [
            [b.x1, b.y1, b.x2, b.y2] for b in person_boxes
        ]
        confirmed_tracks = self._tracker.update(person_coords)
        # confirmed_tracks: list of (track_id, box_array)
 
        # Reorder person_boxes to match confirmed track order
        # tracker returns confirmed tracks which may differ in count
        # from raw person_boxes if some are still tentative
        confirmed_person_boxes = []
        confirmed_track_ids    = []
 
        for track_id, track_box in confirmed_tracks:
            # Find the raw person box closest to this track box by IoU
            best_idx  = -1
            best_iou  = -1.0
            for i, pb in enumerate(person_boxes):
                pb_box = np.array([pb.x1, pb.y1, pb.x2, pb.y2])
                iou    = _box_iou(track_box, pb_box)
                if iou > best_iou:
                    best_iou = iou
                    best_idx = i
            if best_idx >= 0 and best_iou > 0.1:
                confirmed_person_boxes.append(person_boxes[best_idx])
                confirmed_track_ids.append(track_id)
 
        # Spatial assignment — PPE items -> persons

        persons = assign_ppe_to_persons(
            person_boxes  = confirmed_person_boxes,
            ppe_detections = ppe_boxes,
            track_ids     = confirmed_track_ids,
            iou_threshold = settings.SPATIAL_IOU_THRESHOLD,
        )
 
        inference_ms = (time.perf_counter() - t0) * 1000
 
        #  Build raw counts for audit

        raw_counts = _count_raw(raw_boxes)
 
        result = PPEFrameResult(
            camera_id        = camera_id,
            frame_number     = frame_number,
            processed_at     = datetime.now(timezone.utc),
            inference_ms     = round(inference_ms, 2),
            persons          = persons,
            raw_person_count = raw_counts["person"],
            raw_helmet_count = raw_counts["helmet"],
            raw_vest_count   = raw_counts["vest"],
            raw_gloves_count = raw_counts["gloves"],
            raw_boots_count  = raw_counts["boots"],
        )
 
        logger.debug(
            "PPE inference complete",
            extra={
                "camera_id":    camera_id,
                "frame_number": frame_number,
                "persons":      len(persons),
                "violations":   result.non_compliant_count,
                "inference_ms": round(inference_ms, 2),
            },
        )
 
        return result
 
 
    def __repr__(self) -> str:
        return (
            f"<FallDetector max_age={self.max_age_s} "
            f"min_hits={self.min_hits} "
            f"iou_threshold={self.iou_threshold}>"
        )
 
    def __str__(self) -> str:
        return (
            f"FallDetector(max_age={self.max_age_s}, "
            f"min_hits={self.min_hits}, "
            f"iou_threshold={self.iou_threshold})"
        )