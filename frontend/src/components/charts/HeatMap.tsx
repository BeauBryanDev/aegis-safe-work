import { useMemo } from "react"

interface Props {
  rows?: number
  cols?: number
  /** optional fixed matrix (0–1 values); generated if omitted */
  matrix?: number[][]
}

/**
 * Temporal attention map (bottom-left of the mockup — "FRAME POSITION vs
 * SLIDING WINDOW INDEX"). A CSS-grid heatmap; brighter orange = higher
 * attention. Pure presentation, fed mock intensities by default.
 */
const HeatMap = ({ rows = 8, cols = 24, matrix }: Props) => {
  const data = useMemo<number[][]>(() => {
    if (matrix) return matrix
    return Array.from({ length: rows }, (_, r) =>
      Array.from({ length: cols }, (_, c) => {
        // a wandering bright band through the middle rows
        const band = Math.exp(-Math.pow((r - rows / 2) / 1.6, 2))
        const sweep = Math.exp(-Math.pow((c - (cols / 2 + Math.sin(r) * 4)) / 5, 2))
        return Math.min(1, band * sweep + Math.random() * 0.25)
      })
    )
  }, [rows, cols, matrix])

  return (
    <div className="flex flex-col gap-[2px]">
      {data.map((row, r) => (
        <div key={r} className="flex gap-[2px]">
          {row.map((v, c) => (
            <div
              key={c}
              className="h-3 flex-1 rounded-[1px]"
              style={{
                background: `rgba(255, 106, 0, ${0.08 + v * 0.92})`,
                boxShadow: v > 0.7 ? "0 0 5px rgba(255,106,0,0.8)" : "none",
              }}
              title={`f${c} / w${r}: ${(v * 100).toFixed(0)}%`}
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export default HeatMap
