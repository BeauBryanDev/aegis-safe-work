import { useEffect, useState } from "react"
import { RawYOLODetection } from "../types/detection.types"

export const useInference = () => {
  const [detections, setDetections] = useState<RawYOLODetection[]>([])

  useEffect(() => {
    const interval = setInterval(() => {
      //  Simulate detections
      setDetections([
        {
          x: 100,
          y: 120,
          width: 80,
          height: 150,
          confidence: 0.92,
          classId: 0,
        },
        {
          x: 300,
          y: 200,
          width: 100,
          height: 100,
          confidence: 0.87,
          classId: 7, // fall
        },
      ])
    }, 500)

    return () => clearInterval(interval)
  }, [])

  return { detections }
}