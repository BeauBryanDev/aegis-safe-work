import { useEffect, useState } from "react"

/** Ticking clock for the HUD header. Updates every `intervalMs`. */
export const useClock = (intervalMs = 1000) => {
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])

  return now
}

/** "14:37:42" style 24h timestamp. */
export const formatClock = (d: Date) =>
  d.toLocaleTimeString("en-GB", { hour12: false })

/** "2027-03-14" style date stamp. */
export const formatDate = (d: Date) => d.toISOString().slice(0, 10)
