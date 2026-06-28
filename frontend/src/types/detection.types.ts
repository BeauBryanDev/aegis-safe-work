export type DetectionClass =
  | "person"
  | "helmet"
  | "vest"
  | "boots"
  | "gloves"
  | "fire"
  | "smoke"
  | "fall"

export interface RawYOLODetection {
  x: number
  y: number
  width: number
  height: number
  confidence: number
  classId: number
}

export interface Detection {
  bbox: {
    x: number
    y: number
    width: number
    height: number
  }
  label: DetectionClass
  confidence: number
  color: string
}