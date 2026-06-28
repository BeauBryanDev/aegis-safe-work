import { create } from "zustand"
import { SafetyAlert } from "../types/alert.types"

interface AlertState {
  alerts: SafetyAlert[]
  addAlert: (alert: SafetyAlert) => void
  acknowledge: (id: string) => void
  acknowledgeAll: () => void
  clear: () => void
  /** newest first, capped */
  setAlerts: (alerts: SafetyAlert[]) => void
}

const MAX_ALERTS = 100

export const useAlertStore = create<AlertState>((set) => ({
  alerts: [],

  addAlert: (alert) =>
    set((state) => ({
      alerts: [alert, ...state.alerts].slice(0, MAX_ALERTS),
    })),

  acknowledge: (id) =>
    set((state) => ({
      alerts: state.alerts.map((a) =>
        a.id === id ? { ...a, acknowledged: true } : a
      ),
    })),

  acknowledgeAll: () =>
    set((state) => ({
      alerts: state.alerts.map((a) => ({ ...a, acknowledged: true })),
    })),

  clear: () => set({ alerts: [] }),

  setAlerts: (alerts) => set({ alerts: alerts.slice(0, MAX_ALERTS) }),
}))

/** Selector: count of unacknowledged alerts. */
export const selectUnacknowledged = (state: AlertState) =>
  state.alerts.filter((a) => !a.acknowledged).length
