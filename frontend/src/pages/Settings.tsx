import { useState } from "react"
import Card from "../components/ui/Card"
import CyberOrangeButton from "../components/ui/CyberOrangeButton"

interface Toggle {
  key: string
  label: string
  desc: string
  on: boolean
}

const INITIAL: Toggle[] = [
  { key: "fire", label: "Fire / Smoke Detection", desc: "Client-side YOLOv8n (ONNX.JS)", on: true },
  { key: "ppe", label: "PPE Compliance", desc: "Backend YOLOv11s", on: true },
  { key: "fall", label: "Fall Detection", desc: "Backend EfficientNet+MLP", on: true },
  { key: "sound", label: "Audible Alarms", desc: "Play sound on critical alerts", on: false },
]

const Row = ({ t, onToggle }: { t: Toggle; onToggle: () => void }) => (
  <div className="flex items-center justify-between border-b border-cyber-orange/10 py-3">
    <div className="leading-tight">
      <span className="block text-xs uppercase tracking-widest text-cyber-orange/90">
        {t.label}
      </span>
      <span className="block text-[0.6rem] uppercase tracking-wider text-cyber-amber/60">
        {t.desc}
      </span>
    </div>
    <button
      onClick={onToggle}
      className={`relative h-5 w-10 rounded-full border transition-colors ${
        t.on ? "border-cyber-orange bg-cyber-orange/30" : "border-cyber-orange/30 bg-black"
      }`}
    >
      <span
        className={`absolute top-0.5 h-3.5 w-3.5 rounded-full transition-all ${
          t.on ? "left-5 bg-cyber-orange shadow-[0_0_6px_#ff6a00]" : "left-0.5 bg-cyber-orange/40"
        }`}
      />
    </button>
  </div>
)

const Settings = () => {
  const [toggles, setToggles] = useState(INITIAL)
  const [threshold, setThreshold] = useState(0.75)

  const flip = (key: string) =>
    setToggles((prev) => prev.map((t) => (t.key === key ? { ...t, on: !t.on } : t)))

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-3">
      <Card title="Detection Modules">
        {toggles.map((t) => (
          <Row key={t.key} t={t} onToggle={() => flip(t.key)} />
        ))}
      </Card>

      <Card title="Fall Alert Threshold">
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={0}
            max={1}
            step={0.01}
            value={threshold}
            onChange={(e) => setThreshold(Number(e.target.value))}
            className="flex-1 accent-cyber-orange"
          />
          <span className="w-12 text-right text-sm tabular-nums text-cyber-orange text-glow">
            {threshold.toFixed(2)}
          </span>
        </div>
        <p className="mt-2 text-[0.6rem] uppercase tracking-widest text-cyber-orange/50">
          Probability above which a fall raises a critical alert.
        </p>
      </Card>

      <div className="flex justify-end gap-2">
        <CyberOrangeButton variant="outline">Reset</CyberOrangeButton>
        <CyberOrangeButton variant="solid">Save Config</CyberOrangeButton>
      </div>
    </div>
  )
}

export default Settings
