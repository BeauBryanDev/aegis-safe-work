
import numpy as np
 
from app.core.config import settings
from app.schemas.ppes import PersonCompliance, PPEComplianceStatus, RawDetectionBox
 
""" 
Associates individual PPE item detections (helmet, vest, gloves, boots)
to their corresponding person bounding box.
given a set of person boxes and a set of PPE item boxes, determine
which items belong to which person.
"""

# IoU Computation
# Associates individual Subjects PPE item detections (helmet, vest, gloves, boots)

def compute_iou(box_a: tuple, box_b: tuple) -> float:
    """
    Compute Intersection over Union between two bounding boxes.
 
    Args:
        box_a, box_b : (x1, y1, x2, y2) normalized [0, 1]
 
    Returns:
        float : IoU in [0, 1]
    """
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
 
    inter_x1 = max(ax1, bx1)
    inter_y1 = max(ay1, by1)
    inter_x2 = min(ax2, bx2)
    inter_y2 = min(ay2, by2)
 
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
 
    if inter_area == 0.0:
        return 0.0
 
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    union_area = area_a + area_b - inter_area
 
    if union_area <= 0.0:
        return 0.0
 
    return inter_area / union_area
 

def compute_containment(item_box: tuple, person_box: tuple) -> float:
    """
    Compute what fraction of the item box is contained within the person box.
    Useful for small PPE items (gloves, boots) where IoU can be low even when
    the item is clearly within the person's bounds.
 
    Returns:
        float : fraction of item area inside person box, in [0, 1]
    """
    ix1, iy1, ix2, iy2 = item_box
    px1, py1, px2, py2 = person_box
 
    inter_x1 = max(ix1, px1)
    inter_y1 = max(iy1, py1)
    inter_x2 = min(ix2, px2)
    inter_y2 = min(iy2, py2)
 
    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
 
    item_area = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if item_area <= 0.0:
        return 0.0
 
    return inter_area / item_area
 
 
 # Main Function 
 
def assign_ppe_to_persons(
    person_boxes:  list[RawDetectionBox],
    ppe_detections: list[RawDetectionBox],
    track_ids:     list[int],
    iou_threshold: float | None = None,
) -> list[PersonCompliance]:
    """
    Assign PPE item detections to person bounding boxes.
 
    Args:
        person_boxes   : list of RawDetectionBox for class Person
        ppe_detections : list of RawDetectionBox for all PPE classes
                         (helmet, no_helmet, vest, no_vest, gloves,
                          no_gloves, boots — no_* classes ignored here,
                          positive presence only)
        track_ids      : tracker-assigned IDs, one per person_box in order
        iou_threshold  : minimum IoU (or containment) to assign item to person.
                         Defaults to settings.SPATIAL_IOU_THRESHOLD (0.15).
 
    Returns:
        list[PersonCompliance] : one entry per person with PPE flags set
    """
    threshold = iou_threshold or settings.SPATIAL_IOU_THRESHOLD
 
    # PPE class names that indicate presence (ignore no_* classes)
    POSITIVE_PPE = {
        settings.PPE_CLASS_HELMET:  "helmet",
        settings.PPE_CLASS_GLOVES:  "gloves",
        settings.PPE_CLASS_VEST:    "vest",
        settings.PPE_CLASS_BOOTS:   "boots",
        settings.PPE_CLASS_GOGGLES: "goggles",
    }
    # Initialize compliance state per person
    # Counters track raw detections before caps are applied
    persons: list[dict] = []
    for i, person in enumerate(person_boxes):
        persons.append({
            "track_id":    track_ids[i] if i < len(track_ids) else i,
            "x1":          person.x1,
            "y1":          person.y1,
            "x2":          person.x2,
            "y2":          person.y2,
            "conf":        person.confidence,
            "has_helmet":  False,
            "has_vest":    False,
            "has_gloves":  False,
            "has_boots":   False,
            "has_goggles": False,
            "gloves_count": 0,
            "boots_count":  0,
        })
 
    # Assign each PPE item to the best matching person
    for item in ppe_detections:
        if item.class_id not in POSITIVE_PPE:
            continue
 
        item_box  = (item.x1, item.y1, item.x2, item.y2)
        best_idx  = -1
        best_score = 0.0
 
        for i, person in enumerate(person_boxes):
            person_box = (person.x1, person.y1, person.x2, person.y2)
 
            # Use max(IoU, containment) as the assignment score.
            # Containment handles small items (gloves, boots) that may have
            # low IoU with the full person box but are clearly inside it.
            iou         = compute_iou(item_box, person_box)
            containment = compute_containment(item_box, person_box)
            score       = max(iou, containment)
 
            if score > best_score:
                best_score = score
                best_idx   = i
 
        if best_idx == -1 or best_score < threshold:
            continue
 
        class_name = POSITIVE_PPE[item.class_id]
 
        if class_name == "helmet":
            persons[best_idx]["has_helmet"] = True
        elif class_name == "vest":
            persons[best_idx]["has_vest"] = True
        elif class_name == "gloves":
            persons[best_idx]["gloves_count"] += 1
        elif class_name == "boots":
            persons[best_idx]["boots_count"] += 1
 
    # Apply overcounting caps and build PersonCompliance objects
    results: list[PersonCompliance] = []
    for p in persons:
        has_gloves = p["gloves_count"] >= 1  # at least one glove detected -> present
        has_boots  = p["boots_count"]  >= 1
 
        # Cap raw counts for logging 
        gloves_capped = min(p["gloves_count"], settings.MAX_GLOVES_PER_PERSON)
        boots_capped  = min(p["boots_count"],  settings.MAX_BOOTS_PER_PERSON)
 
        compliance = PersonCompliance(
            track_id   = p["track_id"],
            x1         = p["x1"],
            y1         = p["y1"],
            x2         = p["x2"],
            y2         = p["y2"],
            conf       = p["conf"],
            has_helmet = p["has_helmet"],
            has_vest   = p["has_vest"],
            has_gloves = has_gloves,
            has_boots  = has_boots,
        )
        results.append(compliance)
 
    return results
 
 
# Filter raw detections by class group

def split_detections(
    raw_boxes: list[RawDetectionBox],
) -> tuple[list[RawDetectionBox], list[RawDetectionBox]]:
    """
    Split a flat list of YOLO detections into:
        (person_boxes, ppe_boxes)
 
    Args:
        raw_boxes : all detections from YOLOv11s for one frame
 
    Returns:
        person_boxes : detections where class_id == PPE_CLASS_PERSON
        ppe_boxes    : all other detections (PPE items, positive and negative)
    """
    person_boxes = [b for b in raw_boxes if b.class_id == settings.PPE_CLASS_PERSON]
    ppe_boxes    = [b for b in raw_boxes if b.class_id != settings.PPE_CLASS_PERSON]
    
    return person_boxes, ppe_boxes
 
 