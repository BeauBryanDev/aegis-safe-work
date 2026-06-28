import { Detection } from "../../types/detection.types"

interface RenderOptions {
  ctx: CanvasRenderingContext2D
  detections: Detection[]
}

export const renderBoundingBoxes = ({ ctx, detections }: RenderOptions) => {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)

  detections.forEach((det) => {
    const { x, y, width, height } = det.bbox

    // Box
    ctx.strokeStyle = det.color
    ctx.lineWidth = 2
    ctx.shadowColor = det.color
    ctx.shadowBlur = 10
    ctx.strokeRect(x, y, width, height)

    // Label background
    const text = `${det.label} ${(det.confidence * 100).toFixed(0)}%`
    ctx.font = "12px monospace"
    const textWidth = ctx.measureText(text).width

    ctx.fillStyle = det.color
    ctx.fillRect(x, y - 16, textWidth + 6, 14)

    // Label text
    ctx.fillStyle = "#000"
    ctx.fillText(text, x + 3, y - 4)

    // Reset shadow (important for perf)
    ctx.shadowBlur = 0
  })
}