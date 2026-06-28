import { ReactNode } from "react"
import Card from "../ui/Card"

export type KPITone = "orange" | "green" | "red" | "amber"

const VALUE_TONE: Record<KPITone, string> = {
  orange: "text-cyber-orange text-glow",
  amber: "text-cyber-amber",
  green: "text-[#00ff9c] [text-shadow:0_0_8px_#00ff9c]",
  red: "text-[#ff3b3b] [text-shadow:0_0_8px_#ff3b3b]",
}

interface KPICardProps {
  label: string
  value: ReactNode
  unit?: string
  icon?: ReactNode
  tone?: KPITone
  /** optional sparkline / mini-content under the value */
  footer?: ReactNode
  alert?: boolean
}

/** Base KPI tile used by every dashboard metric card. */
const KPICard = ({
  label,
  value,
  unit,
  icon,
  tone = "orange",
  footer,
  alert,
}: KPICardProps) => {
  return (
    <Card className={`min-h-[96px] ${alert ? "pulse" : ""}`}>
      <div className="flex items-start justify-between">
        <span className="text-[0.65rem] uppercase tracking-[0.15em] text-cyber-orange/70">
          {label}
        </span>
        {icon && <span className="text-cyber-orange/80">{icon}</span>}
      </div>

      <div className="mt-1 flex items-baseline gap-1">
        <span className={`text-3xl font-bold tabular-nums ${VALUE_TONE[tone]}`}>
          {value}
        </span>
        {unit && (
          <span className="text-xs text-cyber-orange/60">{unit}</span>
        )}
      </div>

      {footer && <div className="mt-2">{footer}</div>}
    </Card>
  )
}

export default KPICard
