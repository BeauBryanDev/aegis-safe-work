import { useEffect } from "react"
import { useDetectionStore } from "../stores/useDetectionStore"
import { useAlertStore } from "../stores/useAlertStore"
import { useAppStore } from "../stores/useAppStore"
import {
  genAlert,
  genPPEBreakdown,
  randInt,
  seedAlerts,
} from "../services/mockData"

/**
 * Mock telemetry driver. Mount ONCE near the app root. Seeds the global stores
 * and then periodically mutates them so the whole HUD feels live without a
 * backend. Replace with real WebSocket / inference wiring later.
 */
export const useTelemetry = () => {
  const detection = useDetectionStore
  const alerts = useAlertStore
  const app = useAppStore

  useEffect(() => {
    // --- seed ---
    alerts.getState().setAlerts(seedAlerts())
    const breakdown0 = genPPEBreakdown()
    detection.getState().setPPEBreakdown(breakdown0)
    detection.getState().setPeopleCount(randInt(1, 5))

    // --- detection + metrics tick (1s) ---
    const detTimer = setInterval(() => {
      const d = detection.getState()
      d.setPeopleCount(Math.max(0, d.peopleCount + randInt(-1, 1)))

      const breakdown = genPPEBreakdown()
      d.setPPEBreakdown(breakdown)
      const avg =
        (breakdown.helmet + breakdown.vest + breakdown.boots + breakdown.gloves) /
        4
      d.setPPECompliance(Math.round(avg))

      const fall = Math.random() < 0.12
      const fire = Math.random() < 0.08
      d.setFallDetected(fall)
      d.setFireDetected(fire)
      if (fall) d.setFallCount(d.fallCount + 1)
      if (fire) d.setFireCount(d.fireCount + 1)

      app.getState().setMetrics({
        latencyMs: randInt(18, 60),
        systemLoad: randInt(35, 85),
        uptimeSeconds: Math.floor((Date.now() - app.getState().bootedAt) / 1000),
      })
    }, 1000)

    // --- alert feed tick (~every 6s) ---
    const alertTimer = setInterval(() => {
      if (Math.random() < 0.6) alerts.getState().addAlert(genAlert())
    }, 6000)

    return () => {
      clearInterval(detTimer)
      clearInterval(alertTimer)
    }
  }, [detection, alerts, app])
}
