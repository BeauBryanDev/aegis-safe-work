import time
from dataclasses import dataclass, field
 
import numpy as np
from scipy.optimize import linear_sum_assignment
 
from app.core.config import settings
from app.core.logging import get_logger
 
logger = get_logger(__name__)
 
""" 
Lightweight SORT-style tracker (IoU-based) for assigning persistent
track_ids to person bounding boxes across frames.
Keeps the fall detector's frame buffer coherent: the same physical
person must map to the same track_id across consecutive frames so
the 16-frame buffer accumulates temporally consistent crops.
Tracks confirmed after MIN_HITS detections to avoid spurious IDs
from low-confidence YOLO boxes that appear for one frame only
Tracks dropped after MAX_AGE consecutive frames without a match
"""

@dataclass
class Track:
    """
    Represents one tracked person across frames.
 
    States:
        tentative  — seen fewer than MIN_HITS times, not yet confirmed
        confirmed  — seen >= MIN_HITS times, actively tracked
        lost       — missed for >= 1 frame, still alive up to MAX_AGE misses
    """
    track_id:   int
    box:        np.ndarray  # (4,) float32 [x1, y1, x2, y2] normalized
    hits:       int  = 1  # total matched detections
    age:        int  = 0  # consecutive frames without a match
    is_confirmed: bool = False
    last_seen:  float = field(default_factory=time.monotonic)
 
 
    def update(self, box: np.ndarray) -> None:
        """Update track with a new matched detection box."""
        self.box          = box.astype(np.float32)
        self.hits        += 1
        self.age          = 0
        self.last_seen    = time.monotonic()
        
        if self.hits >= settings.TRACKER_MIN_HITS:
            
            self.is_confirmed = True
 
 
    def mark_missed(self) -> None:
        """Increment miss counter when no detection matched this track."""
        self.age += 1
 
    @property
    def is_lost(self) -> bool:
        
        return self.age >= settings.TRACKER_MAX_AGE
 
    def __repr__(self) -> str:
        
        state = "confirmed" if self.is_confirmed else "tentative"
        
        return (
            f"<Track id={self.track_id} hits={self.hits} "
            f"age={self.age} state={state}>"
        )
 
 
# IoU-based tracker Matrix Computation

def iou_matrix(
    detections: np.ndarray,
    tracks:     np.ndarray,
) -> np.ndarray:
    """
    Compute pairwise IoU between detection boxes and track boxes.
 
    Args:
        detections : (N, 4) float32 [x1, y1, x2, y2] normalized
        tracks     : (M, 4) float32 [x1, y1, x2, y2] normalized
 
    Returns:
        np.ndarray : (N, M) float32 IoU matrix
    """
    n = len(detections)
    m = len(tracks)
 
    if n == 0 or m == 0:
        
        return np.zeros((n, m), dtype=np.float32)
 
    # Expand for broadcasting: (N, 1, 4) and (1, M, 4)
    det = detections[:, np.newaxis, :]  # (N, 1, 4)
    trk = tracks[np.newaxis, :, :]     # (1, M, 4)
 
    inter_x1 = np.maximum(det[..., 0], trk[..., 0])
    inter_y1 = np.maximum(det[..., 1], trk[..., 1])
    inter_x2 = np.minimum(det[..., 2], trk[..., 2])
    inter_y2 = np.minimum(det[..., 3], trk[..., 3])
 
    inter_w   = np.maximum(0.0, inter_x2 - inter_x1)
    inter_h   = np.maximum(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
 
    area_det  = ((detections[:, 2] - detections[:, 0]) *
                 (detections[:, 3] - detections[:, 1]))[:, np.newaxis]
    area_trk  = ((tracks[:, 2] - tracks[:, 0]) *
                 (tracks[:, 3] - tracks[:, 1]))[np.newaxis, :]
 
    union_area = area_det + area_trk - inter_area
    union_area = np.maximum(union_area, 1e-6)
 
    return (inter_area / union_area).astype(np.float32)
 
 
# Hungarian matching

def match_detections_to_tracks(
    detections:    np.ndarray,
    track_boxes:   np.ndarray,
    iou_threshold: float,
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """
    Optimal one-to-one assignment of detections to existing tracks
    using the Hungarian algorithm on the IoU cost matrix.
 
    Args:
        detections    : (N, 4) detection boxes
        track_boxes   : (M, 4) current track boxes
        iou_threshold : minimum IoU to accept a match
 
    Returns:
        matches       : list of (detection_idx, track_idx) pairs
        unmatched_det : list of detection indices with no track match
        unmatched_trk : list of track indices with no detection match
    """
    if len(detections) == 0:
        return [], [], list(range(len(track_boxes)))
 
    if len(track_boxes) == 0:
        return [], list(range(len(detections))), []
 
    iou_mat = iou_matrix(detections, track_boxes)   # (N, M)
 
    # Hungarian algorithm minimizes cost — use 1 - IoU as cost
    cost_mat = 1.0 - iou_mat
    row_ind, col_ind = linear_sum_assignment(cost_mat)
 
    matches        = []
    unmatched_det  = list(range(len(detections)))
    unmatched_trk  = list(range(len(track_boxes)))
 
    for r, c in zip(row_ind, col_ind):
        
        if iou_mat[r, c] >= iou_threshold:
            matches.append((int(r), int(c)))
            unmatched_det.remove(r)
            unmatched_trk.remove(c)
 
    return matches, unmatched_det, unmatched_trk
 
 
# Tracker 

class PersonTracker:
    """
    IoU-based multi-object tracker for person detections.
    One instance lives on app.state.tracker for the FastAPI app lifetime.
 
    Usage per frame:
    track_results = tracker.update(person_boxes_normalized)
    # track_results: list of (track_id, box) for confirmed tracks only
    """
 
    def __init__(
        self,
        max_age:       int   = settings.TRACKER_MAX_AGE,
        min_hits:      int   = settings.TRACKER_MIN_HITS,
        iou_threshold: float = settings.TRACKER_IOU_THRESHOLD,
    ):
        self.max_age       = max_age
        self.min_hits      = min_hits
        self.iou_threshold = iou_threshold
        self._tracks:  list[Track] = []
        self._next_id: int         = 1
        self._frame_count: int     = 0
 
 
    # Main update — call once per frame
 
    def update(
        self,
        detections: list[list[float]] | np.ndarray,
    ) -> list[tuple[int, np.ndarray]]:
        """
        Update tracker state with new person detections for this frame.
 
        Args:
            detections : (N, 4) array or list of [x1, y1, x2, y2] boxes,
                         normalized [0, 1]. Pass empty list if no persons
                         detected in this frame.
 
        Returns:
            list of (track_id, box) for all CONFIRMED active tracks.
            Tentative tracks (hits < MIN_HITS) are excluded from output
            to avoid feeding unstable crops to the fall detector.
        """
        self._frame_count += 1
        det_array = (
            np.array(detections, dtype=np.float32)
            
            if len(detections) > 0
            
            else np.empty((0, 4), dtype=np.float32)
        )
 
        track_boxes = (
            np.array([t.box for t in self._tracks], dtype=np.float32)
            
            if self._tracks
            
            else np.empty((0, 4), dtype=np.float32)
        )
 
        matches, unmatched_det, unmatched_trk = match_detections_to_tracks(
            det_array, track_boxes, self.iou_threshold
        )
 
        # Update matched tracks
        for det_idx, trk_idx in matches:
            self._tracks[trk_idx].update(det_array[det_idx])
 
        # Mark unmatched tracks as missed
        for trk_idx in unmatched_trk:
            self._tracks[trk_idx].mark_missed()
 
        # Spawn new tracks for unmatched detections
        for det_idx in unmatched_det:
            
            new_track = Track(
                track_id = self._next_id,
                box      = det_array[det_idx].astype(np.float32),
            )
            self._tracks.append(new_track)
            self._next_id += 1
            logger.debug(
                "New track spawned",
                extra={"track_id": new_track.track_id},
            )
 
        # Evict lost tracks
        lost = [t for t in self._tracks if t.is_lost]
        
        for t in lost:
            
            logger.debug(
                "Track lost and evicted",
                extra={"track_id": t.track_id, "hits": t.hits},
            )
        self._tracks = [t for t in self._tracks if not t.is_lost]
 
        # Return confirmed tracks only
        return [
            (t.track_id, t.box)
            for t in self._tracks
            if t.is_confirmed
        ]
 
    # Accessors
 
    @property
    def active_track_ids(self) -> list[int]:
        return [t.track_id for t in self._tracks if t.is_confirmed]
 
    @property
    def active_count(self) -> int:
        return len([t for t in self._tracks if t.is_confirmed])
 
    def reset(self) -> None:
        """Reset tracker state. Useful for camera stream reconnections."""
        self._tracks     = []
        self._next_id    = 1
        self._frame_count = 0
        logger.info("PersonTracker reset.")
 
    def status(self) -> list[dict]:
        """Snapshot of all tracks for the /health endpoint."""
        return [
            {
                "track_id":    t.track_id,
                "confirmed":   t.is_confirmed,
                "hits":        t.hits,
                "age":         t.age,
                "box":         t.box.tolist(),
                "idle_s":      round(time.monotonic() - t.last_seen, 2),
            }
            for t in self._tracks
        ]
 
    def __repr__(self) -> str:
        return (
            f"<PersonTracker active={self.active_count} "
            f"total_tracks={len(self._tracks)} "
            f"frames={self._frame_count}>"
        )