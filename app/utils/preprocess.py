import cv2
import numpy as np
 
from app.core.config import settings
 
PPE_INPUT_SIZE = 640

""" 
Pipeline:
Prepares raw BGR frames from the video stream for YOLOv11s inference.
BGR frame (any resolution)
-> letterbox resize to 640x640 (black padding, aspect ratio preserved)
-> BGR -> RGB
-> float32 / 255.0  (normalize to [0, 1])
-> HWC -> NCHW transpose
-> add batch dim
-> (1, 3, 640, 640) float32  ready for ONNX Runtime

"""

# Letterbox for YOLov11small 640x640 input size

def letterbox_ppe(
    frame_bgr: np.ndarray,
    target: int = PPE_INPUT_SIZE,
) -> tuple[np.ndarray, float, tuple[int, int]]:
    """
    Resize a BGR frame to (target x target) with black padding,
    preserving aspect ratio. Returns the padded RGB frame plus
    metadata needed to map detections back to original coordinates.
 
    Args:
        frame_bgr : OpenCV BGR frame, any resolution
        target    : model input size (default 640)
 
    Returns:
        padded_rgb : (target, target, 3) uint8 RGB
        scale      : float — scale factor applied (same for both axes)
        pad        : (pad_left, pad_top) — pixel offsets of the content area
                     within the padded canvas. Used by decode_boxes() to
                     remap normalized YOLO output back to original frame coords.
    """
    h, w  = frame_bgr.shape[:2]
    scale = target / max(h, w)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
 
    resized  = cv2.resize(frame_bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    canvas   = np.zeros((target, target, 3), dtype=np.uint8)
    
    pad_top  = (target - new_h) // 2
    pad_left = (target - new_w) // 2
    
    canvas[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = resized
 
    padded_rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
    
    return padded_rgb, scale, (pad_left, pad_top)
 
 
# BUILD ONNX IMPUT TENSOR FOR PPE MODEL

def preprocess_frame_ppe(
    frame_bgr: np.ndarray,
    target: int = PPE_INPUT_SIZE,
) -> tuple[np.ndarray, float, tuple[int, int]]:
    """
    Full preprocessing pipeline for a single frame destined for YOLOv11s.
 
    Args:
        frame_bgr : raw OpenCV BGR frame from the video stream
        target    : model input size (default 640)
 
    Returns:
        tensor    : (1, 3, 640, 640) float32 in [0, 1] — ONNX Runtime input
        scale     : scale factor applied during letterbox resize
        pad       : (pad_left, pad_top) pixel offsets for coordinate remapping
    """
    padded_rgb, scale, pad = letterbox_ppe(frame_bgr, target)
 
    # float32 / 255.0 — YOLO standard normalization (no mean/std subtraction)
    normalized = padded_rgb.astype(np.float32) / 255.0
 
    # HWC -> CHW -> NCHW
    chw    = normalized.transpose(2, 0, 1)          # (3, 640, 640)
    tensor = np.expand_dims(chw, axis=0)            # (1, 3, 640, 640)
 
    return tensor, scale, pad
 
 
# Remppaing detections back to original frame coordinates

def decode_boxes(
    boxes_xyxy: np.ndarray,
    scale: float,
    pad: tuple[int, int],
    orig_shape: tuple[int, int],
) -> np.ndarray:
    """
    Remap bounding boxes from the 640x640 letterboxed space back to
    the original frame resolution, then normalize to [0, 1].
 
    YOLO outputs boxes in pixel coordinates relative to the 640x640
    padded input. This function:
        1. Subtracts the letterbox padding offsets
        2. Divides by the scale factor to recover original pixel coords
        3. Clips to frame boundaries
        4. Normalizes to [0, 1] relative to original frame dimensions
 
    Args:
        boxes_xyxy : (N, 4) float32 — [x1, y1, x2, y2] in 640x640 pixel space
        scale      : scale factor from letterbox_ppe()
        pad        : (pad_left, pad_top) from letterbox_ppe()
        orig_shape : (height, width) of the original frame before preprocessing
 
    Returns:
        np.ndarray : (N, 4) float32 — [x1, y1, x2, y2] normalized to [0, 1]
    """
    pad_left, pad_top = pad
    orig_h, orig_w    = orig_shape
 
    boxes = boxes_xyxy.copy().astype(np.float32)
 
    # Remove padding offsets
    boxes[:, 0] -= pad_left   # x1
    boxes[:, 1] -= pad_top    # y1
    boxes[:, 2] -= pad_left   # x2
    boxes[:, 3] -= pad_top    # y2
 
    # Undo scale
    boxes /= scale
 
    # Clip to original frame boundaries
    boxes[:, 0] = np.clip(boxes[:, 0], 0, orig_w)
    boxes[:, 1] = np.clip(boxes[:, 1], 0, orig_h)
    boxes[:, 2] = np.clip(boxes[:, 2], 0, orig_w)
    boxes[:, 3] = np.clip(boxes[:, 3], 0, orig_h)
 
    # Normalize to [0, 1]
    boxes[:, [0, 2]] /= orig_w
    boxes[:, [1, 3]] /= orig_h
 
    return boxes
 
 
 # Decode YOLOv11s detections back to original frame coordinates

def decode_yolo_output(
    output: np.ndarray,
    scale: float,
    pad: tuple[int, int],
    orig_shape: tuple[int, int],
    conf_threshold: float | None = None,
    iou_threshold:  float | None = None,
) -> list[dict]:
    """
    Parse the raw ONNX output from YOLOv11s into a flat list of detections.
 
    YOLOv11s output shape: (1, 15, 8400)
        - 15 = 4 (box xywh) + 11 (class scores)
        - 8400 = number of anchor predictions
 
    Args:
        output         : raw ONNX Runtime output (1, 15, 8400) float32
        scale          : from preprocess_frame_ppe()
        pad            : from preprocess_frame_ppe()
        orig_shape     : (height, width) of the original frame
        conf_threshold : minimum class confidence (default settings.PPE_CONF_THRESHOLD)
        iou_threshold  : NMS IoU threshold (default settings.PPE_IOU_THRESHOLD)
 
    Returns:
        list of dicts with keys:
            class_id, class_name, confidence, x1, y1, x2, y2
            (coordinates normalized to [0, 1] relative to original frame)
    """
    conf_thr = conf_threshold or settings.PPE_CONF_THRESHOLD
    iou_thr  = iou_threshold  or settings.PPE_IOU_THRESHOLD
 
    CLASS_NAMES = [
        "helmet", "gloves", "vest", "boots", "goggles",
        "none", "Person",
        "no_helmet", "no_goggle", "no_gloves", "no_boots",
    ]
 
    # output: (1, 15, 8400) -> squeeze to (15, 8400) -> transpose to (8400, 15)
    pred = output[0].transpose(1, 0)   # (8400, 15)
 
    boxes_xywh  = pred[:, :4]          # (8400, 4)
    class_scores = pred[:, 4:]         # (8400, 11)
 
    class_ids    = np.argmax(class_scores, axis=1)    # (8400,)
    confidences  = class_scores[np.arange(len(class_scores)), class_ids]  # (8400,)
 
    # Filter by confidence
    mask = confidences >= conf_thr
    if not np.any(mask):
        return []
 
    boxes_xywh  = boxes_xywh[mask]
    class_ids   = class_ids[mask]
    confidences = confidences[mask]
 
    # xywh (center format) -> xyxy (corner format) in 640x640 pixel space
    cx, cy, bw, bh = boxes_xywh[:, 0], boxes_xywh[:, 1], boxes_xywh[:, 2], boxes_xywh[:, 3]
    x1 = cx - bw / 2
    y1 = cy - bh / 2
    x2 = cx + bw / 2
    y2 = cy + bh / 2
    boxes_xyxy = np.stack([x1, y1, x2, y2], axis=1)  # (N, 4)
 
    # Remap to original frame coords, normalized [0, 1]
    boxes_norm = decode_boxes(boxes_xyxy, scale, pad, orig_shape)
 
    # NMS per class via OpenCV (operates on pixel coords, use 640-space boxes)
    results = []
    for cls_id in np.unique(class_ids):
        cls_mask = class_ids == cls_id
        cls_boxes  = boxes_norm[cls_mask]
        cls_confs  = confidences[cls_mask]
 
        # cv2.dnn.NMSBoxes expects [x, y, w, h] in any consistent coord space
        xywh_for_nms = np.column_stack([
            cls_boxes[:, 0],
            cls_boxes[:, 1],
            cls_boxes[:, 2] - cls_boxes[:, 0],
            cls_boxes[:, 3] - cls_boxes[:, 1],
        ]).tolist()
 
        indices = cv2.dnn.NMSBoxes(
            xywh_for_nms,
            cls_confs.tolist(),
            conf_thr,
            iou_thr,
        )
 
        if len(indices) == 0:
            continue
 
        for idx in np.array(indices).flatten():
            results.append({
                "class_id":   int(cls_id),
                "class_name": CLASS_NAMES[int(cls_id)] if int(cls_id) < len(CLASS_NAMES) else "unknown",
                "confidence": float(cls_confs[idx]),
                "x1":         float(cls_boxes[idx, 0]),
                "y1":         float(cls_boxes[idx, 1]),
                "x2":         float(cls_boxes[idx, 2]),
                "y2":         float(cls_boxes[idx, 3]),
            })
 
 
    return results
 