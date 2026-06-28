import { ShieldCheck } from "lucide-react"
import Card from "../ui/Card"
import { useDetectionStore } from "../../stores/useDetectionStore"
import { PPEBreakdown } from "../../types/metrics.types"

const ITEMS: { key: keyof PPEBreakdown; label: string }[] = [
  { key: "helmet", label: "Helmet" },
  { key: "vest", label: "Vest" },
  { key: "boots", label: "Boots" },
  { key: "gloves", label: "Gloves" },
]

const barTone = (pct: number) =>
  pct >= 80 ? "#00ff9c" : pct >= 60 ? "#ffb300" : "#ff3b3b"

const PPEComplianceCard = () => {
  const compliance = useDetectionStore((s) => s.ppeCompliance)
  const breakdown = useDetectionStore((s) => s.ppeBreakdown)

  return (
    <Card title="PPE Compliance" status={<ShieldCheck size={14} />}>
      <div className="mb-3 flex items-baseline gap-1">
        <span
          className="text-4xl font-bold tabular-nums"
          style={{ color: barTone(compliance), textShadow: `0 0 8px ${barTone(compliance)}` }}
        >
          {compliance}
        </span>
        <span className="text-sm text-cyber-orange/60">%</span>
      </div>

      <div className="space-y-1.5">
        {ITEMS.map(({ key, label }) => {
          const pct = breakdown[key]
          return (
            <div key={key} className="flex items-center gap-2">
              <span className="w-12 text-[0.6rem] uppercase tracking-widest text-cyber-orange/70">
                {label}
              </span>
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-cyber-orange/10">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${pct}%`,
                    background: barTone(pct),
                    boxShadow: `0 0 6px ${barTone(pct)}`,
                  }}
                />
              </div>
              <span className="w-9 text-right text-[0.6rem] tabular-nums text-cyber-orange/80">
                {pct}%
              </span>
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default PPEComplianceCard
