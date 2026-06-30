import { useEffect, useRef } from "react"
import { renderBoundingBoxes } from "./BoundingBoxOverlay"
import { adaptYOLODetections } from "../../services/detectionAdapter"
import { RawYOLODetection } from "../../types/detection.types"

interface Props {
  detections: RawYOLODetection[]
  width?: number
  height?: number
}

const LiveStreamCanvas = ({ detections }: Props) => {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true }).then((stream) => {
      if (videoRef.current) {
        videoRef.current.srcObject = stream
      }
    })
  }, [])

  useEffect(() => {
    let animationFrameId: number

    const render = () => {
      const canvas = canvasRef.current
      const video = videoRef.current

      if (!canvas || !video) return

      const ctx = canvas.getContext("2d")
      if (!ctx) return

      canvas.width = video.videoWidth
      canvas.height = video.videoHeight

      const adapted = adaptYOLODetections(
        detections,
        video.videoWidth,
        video.videoHeight,
        canvas.width,
        canvas.height
      )

      renderBoundingBoxes({ ctx, detections: adapted })

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => cancelAnimationFrame(animationFrameId)
  }, [detections])

  return (
    <div className="video-container">
      <video
        ref={videoRef}
        autoPlay
        playsInline
        className="w-full h-full object-cover"
      />
      <canvas
        ref={canvasRef}
        className="video-overlay"
      />
    </div>
  )
}

export default LiveStreamCanvas