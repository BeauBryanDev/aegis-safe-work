import { useEffect, useRef, useState } from "react"
import { HistogramBin, TimePoint } from "../types/metrics.types"
import {
  genFallProbabilitySeries,
  genHistogram,
  rand,
} from "../services/mockData"

/**
 * Rolling mock chart data for the dashboard / metrics pages. The fall series
 * scrolls (drops oldest, appends newest) every `intervalMs`; the histogram is
 * refreshed less often.
 */
export const useChartSeries = (intervalMs = 1500) => {
  const [fallSeries, setFallSeries] = useState<TimePoint[]>(() =>
    genFallProbabilitySeries()
  )
  const [histogram, setHistogram] = useState<HistogramBin[]>(() => genHistogram())
  const tick = useRef(0)

  useEffect(() => {
    const id = setInterval(() => {
      tick.current += 1
      setFallSeries((prev) => {
        const last = prev[prev.length - 1]?.value ?? 0.2
        let next = last + rand(-0.1, 0.1)
        if (Math.random() < 0.1) next += rand(0.2, 0.45)
        next = Math.max(0.02, Math.min(0.98, next))
        const shifted = prev.slice(1)
        return [
          ...shifted,
          { time: (shifted[shifted.length - 1]?.time ?? 0) + 1, value: Number(next.toFixed(3)) },
        ]
      })

      // refresh histogram every ~6s
      if (tick.current % 4 === 0) setHistogram(genHistogram())
    }, intervalMs)

    return () => clearInterval(id)
  }, [intervalMs])

  return { fallSeries, histogram }
}
