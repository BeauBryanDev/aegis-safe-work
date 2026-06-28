import { useEffect, useRef, useState } from "react"

/**
 * Measures real animation-frame throughput. Returns a smoothed FPS value,
 * updated roughly once per second.
 */
export const useFPS = (enabled = true) => {
  const [fps, setFps] = useState(0)
  const frames = useRef(0)
  const last = useRef(performance.now())

  useEffect(() => {
    if (!enabled) return
    let raf: number

    const loop = () => {
      frames.current += 1
      const now = performance.now()
      const elapsed = now - last.current

      if (elapsed >= 1000) {
        setFps(Math.round((frames.current * 1000) / elapsed))
        frames.current = 0
        last.current = now
      }
      raf = requestAnimationFrame(loop)
    }

    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [enabled])

  return fps
}
