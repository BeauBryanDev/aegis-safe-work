import cv2
import numpy as np
 
""" 
ffmpeg equivalent:
scale=224:224:force_original_aspect_ratio=decrease,
pad=224:224:(ow-iw)/2:(oh-ih)/2:color=black
 
"""
# SINGLE SOURCE OF TRUTH

# ImageNet normalization constants ~> ETL Stage II

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
 
TARGET_SIZE   = 224
 

# Main Letterboxing functions Important!
# Never change it unless a trainign v2  perfomed

def letterbox_frame(
    frame_bgr: np.ndarray,
    target: int = TARGET_SIZE,
) -> np.ndarray:
    """
    Resize a BGR frame to (target x target) with black padding,
    preserving aspect ratio. Returns an RGB uint8 array (target, target, 3).
 
    Matches ETL Stage 1 ffmpeg letterbox filter exactly:
    - Proportional scale so the longest side fits within target
    - Center-paste on a black canvas
    - BGR -> RGB conversion
 
    Args:
        frame_bgr : OpenCV frame in BGR format, any resolution
        target    : output size in pixels (default 224)
 
    Returns:
        np.ndarray : (target, target, 3) uint8 RGB
    """
    h, w  = frame_bgr.shape[:2]
    scale = target / max(h, w)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
 
    resized = cv2.resize(
        frame_bgr,
        (new_w, new_h),
        interpolation=cv2.INTER_LINEAR,
    )
 
    canvas   = np.zeros((target, target, 3), dtype=np.uint8)
    pad_top  = (target - new_h) // 2
    pad_left = (target - new_w) // 2
    canvas[pad_top:pad_top + new_h, pad_left:pad_left + new_w] = resized
 
    return cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
 

# Crop a single person From Full Frame and Letterbox

def crop_and_letterbox(
    frame_bgr: np.ndarray,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    target: int = TARGET_SIZE,
    padding_ratio: float = 0.05,
) -> np.ndarray:
    """
    Crop a person bounding box from the full frame, apply a small padding
    margin, then letterbox to (target x target).
 
    Args:
        frame_bgr     : full BGR frame from the video stream
        x1, y1, x2, y2: normalized bbox coordinates in [0, 1]
        target        : output size (default 224)
        padding_ratio : fraction of bbox size to add as margin on each side
                        (default 0.05 = 5%% padding). Prevents cutting off
                        the subject at the exact detection boundary.
 
    Returns:
        np.ndarray : (target, target, 3) uint8 RGB — letterboxed person crop
    """
    fh, fw = frame_bgr.shape[:2]
 
    # Convert normalized coords to absolute pixels
    abs_x1 = int(x1 * fw)
    abs_y1 = int(y1 * fh)
    abs_x2 = int(x2 * fw)
    abs_y2 = int(y2 * fh)
 
    # Apply padding margin
    pad_w = int((abs_x2 - abs_x1) * padding_ratio)
    pad_h = int((abs_y2 - abs_y1) * padding_ratio)
 
    abs_x1 = max(0,  abs_x1 - pad_w)
    abs_y1 = max(0,  abs_y1 - pad_h)
    abs_x2 = min(fw, abs_x2 + pad_w)
    abs_y2 = min(fh, abs_y2 + pad_h)
 
    crop = frame_bgr[abs_y1:abs_y2, abs_x1:abs_x2]
 
    if crop.size == 0:
        # Degenerate box: return black frame rather than crashing
        return np.zeros((target, target, 3), dtype=np.uint8)
 
    rsubject = letterbox_frame(crop, target)
 
    return rsubject


# Normalize Single RGB  frame to ImageNet float32


def normalize_frame(frame_rgb: np.ndarray) -> np.ndarray:
    """
    Apply ImageNet mean/std normalization to a uint8 RGB frame.
 
    Args:
        frame_rgb : (H, W, 3) uint8 RGB in [0, 255]
 
    Returns:
        np.ndarray : (H, W, 3) float32 normalized
    """
    arr = frame_rgb.astype(np.float32) / 255.0
    
    NormalArr = (arr - IMAGENET_MEAN) / IMAGENET_STD
    
    return  NormalArr

# Build a (1, 16, 3, 224, 224) float32 tensor from a list of RGB frames
# Used in order to prepare the frame buffer for ONNX inference


def build_fall_tensor(frames_rgb: list[np.ndarray]) -> np.ndarray:
    """
    Convert a list of 16 letterboxed RGB uint8 frames into the input
    tensor expected by the fall detector ONNX model.
 
    Pipeline:
    list of 16 x (224, 224, 3) uint8
    -> normalize each frame to float32
    -> stack to (16, 224, 224, 3)
    -> transpose to (16, 3, 224, 224)
    -> add batch dim -> (1, 16, 3, 224, 224)
 
    Args:
        frames_rgb : list of exactly 16 (224, 224, 3) uint8 RGB frames
 
    Returns:
        np.ndarray : (1, 16, 3, 224, 224) float32 — ready for ONNX Runtime
    """
    assert len(frames_rgb) == 16, (
        f"build_fall_tensor expects exactly 16 frames, got {len(frames_rgb)}"
    )
 
    normalized = np.stack(
        [normalize_frame(f) for f in frames_rgb],
        axis=0,
    )   # (16, 224, 224, 3) float32
    transposed = normalized.transpose(0, 3, 1, 2) # (16, 3, 224, 224) float32
    
    human_tensor =  np.expand_dims(transposed, axis=0)  # (1, 16, 3, 224, 224) float32
    
    return human_tensor
 