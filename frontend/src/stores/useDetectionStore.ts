import { create } from "zustand"
import { PPEBreakdown } from "../types/metrics.types"

interface DetectionState {
  peopleCount: number
  ppeCompliance: number
  ppeBreakdown: PPEBreakdown
  fallDetected: boolean
  fireDetected: boolean
  fallCount: number
  fireCount: number

  setPeopleCount: (count: number) => void
  setPPECompliance: (value: number) => void
  setPPEBreakdown: (value: PPEBreakdown) => void
  setFallDetected: (value: boolean) => void
  setFireDetected: (value: boolean) => void
  setFallCount: (value: number) => void
  setFireCount: (value: number) => void
}

export const useDetectionStore = create<DetectionState>((set) => ({
  peopleCount: 0,
  ppeCompliance: 0,
  ppeBreakdown: { helmet: 0, vest: 0, boots: 0, gloves: 0 },
  fallDetected: false,
  fireDetected: false,
  fallCount: 0,
  fireCount: 0,

  setPeopleCount: (count) => set({ peopleCount: count }),
  setPPECompliance: (value) => set({ ppeCompliance: value }),
  setPPEBreakdown: (value) => set({ ppeBreakdown: value }),
  setFallDetected: (value) => set({ fallDetected: value }),
  setFireDetected: (value) => set({ fireDetected: value }),
  setFallCount: (value) => set({ fallCount: value }),
  setFireCount: (value) => set({ fireCount: value }),
}))
