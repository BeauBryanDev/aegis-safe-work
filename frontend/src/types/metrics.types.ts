export interface TimePoint {
  /** seconds offset on the X axis */
  time: number
  value: number
}

export interface HistogramBin {
  bin: string
  count: number
}

export interface PPEBreakdown {
  helmet: number
  vest: number
  boots: number
  gloves: number
}

export interface SystemMetrics {
  fps: number
  latencyMs: number
  systemLoad: number
  uptimeSeconds: number
}

export type LogLevel = "INFO" | "WARN" | "ERROR"

export interface SystemLogEntry {
  id: string
  level: LogLevel
  source: string
  message: string
  /** epoch ms */
  timestamp: number
}

export type SystemStatus = "OPERATIONAL" | "DEGRADED" | "OFFLINE"
