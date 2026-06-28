import { create } from "zustand"
import { SystemMetrics, SystemStatus } from "../types/metrics.types"

interface AppState {
  systemStatus: SystemStatus
  /** epoch ms the console booted — used to derive uptime */
  bootedAt: number
  metrics: SystemMetrics

  setSystemStatus: (status: SystemStatus) => void
  setMetrics: (metrics: Partial<SystemMetrics>) => void
}

export const useAppStore = create<AppState>((set) => ({
  systemStatus: "OPERATIONAL",
  bootedAt: Date.now(),
  metrics: {
    fps: 0,
    latencyMs: 0,
    systemLoad: 0,
    uptimeSeconds: 0,
  },

  setSystemStatus: (systemStatus) => set({ systemStatus }),
  setMetrics: (metrics) =>
    set((state) => ({ metrics: { ...state.metrics, ...metrics } })),
}))
