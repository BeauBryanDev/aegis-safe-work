export type AlertSeverity = "critical" | "warning" | "info"

export type AlertType = "fall" | "fire" | "smoke" | "ppe" | "system"

export interface SafetyAlert {
  id: string
  type: AlertType
  severity: AlertSeverity
  message: string
  /** epoch ms */
  timestamp: number
  location?: string
  acknowledged: boolean
}
