/**
 * Mock telemetry generators.
 *
 * Stand-in for the not-yet-built FastAPI backend (PPE + fall models) and for
 * the client-side fire/smoke ONNX model. Everything here is deterministic-ish
 * randomness so the HUD looks "alive" during frontend development.
 */
import { SafetyAlert, AlertSeverity, AlertType } from "../types/alert.types"
import {
  HistogramBin,
  PPEBreakdown,
  SystemLogEntry,
  TimePoint,
  LogLevel,
} from "../types/metrics.types"

const rand = (min: number, max: number) => min + Math.random() * (max - min)
const randInt = (min: number, max: number) => Math.round(rand(min, max))
const pick = <T>(arr: T[]): T => arr[Math.floor(Math.random() * arr.length)]

let idSeq = 0
const nextId = () => `${Date.now().toString(36)}-${(idSeq++).toString(36)}`

/** Fall-probability-over-time series (the big line chart). */
export const genFallProbabilitySeries = (points = 48): TimePoint[] => {
  let value = rand(0.05, 0.2)
  return Array.from({ length: points }, (_, time) => {
    // random walk, clamped to [0, 1], with occasional spikes
    value += rand(-0.08, 0.08)
    if (Math.random() < 0.08) value += rand(0.2, 0.5)
    value = Math.max(0.02, Math.min(0.98, value))
    return { time, value: Number(value.toFixed(3)) }
  })
}

/** Probability distribution histogram (bottom-left of the mockup). */
export const genHistogram = (bins = 12): HistogramBin[] => {
  return Array.from({ length: bins }, (_, i) => {
    const center = i / bins
    // bell-ish curve peaking left-of-center
    const weight = Math.exp(-Math.pow((center - 0.35) * 3, 2))
    return {
      bin: center.toFixed(2),
      count: Math.round(weight * 100 + rand(0, 12)),
    }
  })
}

export const genPPEBreakdown = (): PPEBreakdown => ({
  helmet: randInt(80, 100),
  vest: randInt(80, 100),
  boots: randInt(70, 100),
  gloves: randInt(40, 100),
})

const ALERT_TEMPLATES: Record<AlertType, { severity: AlertSeverity; message: string }> = {
  fall: { severity: "critical", message: "Fall detected — worker down" },
  fire: { severity: "critical", message: "Fire signature detected in frame" },
  smoke: { severity: "warning", message: "Smoke density above threshold" },
  ppe: { severity: "warning", message: "PPE non-compliance: missing gloves" },
  system: { severity: "info", message: "System self-check completed" },
}

const ZONES = ["ZONE-A", "ZONE-B", "ZONE-C", "DOCK-01", "WELD-BAY", "LINE-A"]

export const genAlert = (type?: AlertType, at = Date.now()): SafetyAlert => {
  const t = type ?? pick(["fall", "fire", "smoke", "ppe", "system"] as AlertType[])
  const tpl = ALERT_TEMPLATES[t]
  return {
    id: nextId(),
    type: t,
    severity: tpl.severity,
    message: tpl.message,
    timestamp: at,
    location: pick(ZONES),
    acknowledged: false,
  }
}

/** Seed an initial alert feed (newest first). */
export const seedAlerts = (count = 8): SafetyAlert[] => {
  const now = Date.now()
  return Array.from({ length: count }, (_, i) =>
    genAlert(undefined, now - i * randInt(20_000, 120_000))
  )
}

const LOG_SOURCES = [
  "vision.core",
  "ppe.yolov11s",
  "fire.yolov8n",
  "fall.effnet",
  "stream.rtsp",
  "api.gateway",
]

const LOG_LINES: Record<LogLevel, string[]> = {
  INFO: [
    "frame decoded",
    "inference cycle complete",
    "model warm",
    "heartbeat ok",
    "stream reconnected",
  ],
  WARN: ["latency spike", "dropped frame", "low light conditions", "queue backlog"],
  ERROR: ["inference timeout", "stream disconnected", "decode failure"],
}

export const seedLogs = (count = 24): SystemLogEntry[] => {
  const now = Date.now()
  return Array.from({ length: count }, (_, i) => {
    const level = pick<LogLevel>(
      // weighted: mostly INFO
      ["INFO", "INFO", "INFO", "WARN", "WARN", "ERROR"]
    )
    return {
      id: nextId(),
      level,
      source: pick(LOG_SOURCES),
      message: pick(LOG_LINES[level]),
      timestamp: now - i * randInt(1_000, 8_000),
    }
  })
}

export { rand, randInt, pick }
