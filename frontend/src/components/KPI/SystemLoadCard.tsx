import { Cpu } from "lucide-react"
import Card from "../ui/Card"
import { useAppStore } from "../../stores/useAppStore"

/** System-load KPI with the segmented bar meter from the mockup. */
const SystemLoadCard = () => {
  const load = useAppStore((s) => s.metrics.systemLoad)
  const segments = 20
  const filled = Math.round((load / 100) * segments)

  return (
    <Card>
      <div className="flex items-start justify-between">
        <span className="text-[0.65rem] uppercase tracking-[0.15em] text-cyber-orange/70">
          System Load
        </span>
        <Cpu size={16} className="text-cyber-orange/80" />
      </div>

      <div className="mt-1 flex items-baseline gap-1">
        <span className="text-3xl font-bold tabular-nums text-cyber-orange text-glow">
          {load}
        </span>
        <span className="text-xs text-cyber-orange/60">%</span>
      </div>

      <div className="mt-2 flex gap-[2px]">
        {Array.from({ length: segments }, (_, i) => (
          <span
            key={i}
            className="h-3 flex-1 rounded-[1px]"
            style={{
              background:
                i < filled ? "#ff6a00" : "rgba(255,106,0,0.12)",
              boxShadow: i < filled ? "0 0 4px rgba(255,106,0,0.7)" : "none",
            }}
          />
        ))}
      </div>
    </Card>
  )
}

export default SystemLoadCard
