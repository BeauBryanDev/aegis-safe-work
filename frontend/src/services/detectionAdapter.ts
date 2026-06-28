import { Detection, RawYOLODetection } from "../../types/detection.types"

const CLASS_MAP: Record<number, string> = {
  0: "person",
  1: "helmet",
  2: "vest",
  3: "boots",
  4: "gloves",
  5: "fire",
  6: "smoke",
  7: "fall",
}

const COLOR_MAP: Record<string, string> = {
  person: "#00ff9c",
  helmet: "#00ff9c",
  vest: "#00ff9c",
  boots: "#00ff9c",
  gloves: "#ff3b3b",
  fire: "#ff3b3b",
  smoke: "#ff3b3b",
  fall: "#ff3b3b",
}

export const adaptYOLODetections = (
  raw: RawYOLODetection[],
  imgWidth: number,
  imgHeight: number,
  canvasWidth: number,
  canvasHeight: number
): Detection[] => {
  const scaleX = canvasWidth / imgWidth
  const scaleY = canvasHeight / imgHeight

  return raw.map((det) => {
    const label = CLASS_MAP[det.classId] as Detection["label"]

    return {
      bbox: {
        x: det.x * scaleX,
        y: det.y * scaleY,
        width: det.width * scaleX,
        height: det.height * scaleY,
      },
      label,
      confidence: det.confidence,
      color: COLOR_MAP[label],
    }
  })
}