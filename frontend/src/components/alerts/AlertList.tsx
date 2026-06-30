import { SafetyAlert, AlertSeverity } from "../../types/alert.types"
import { formatClock } from "../../hooks/useClock"

interface Props {
  alerts: SafetyAlert[]
  maxHeight?: number
  onAcknowledge?: (id: string) => void
}

const DOT: Record<AlertSeverity, string> = {
  critical: "bg-[#ff3b3b] shadow-[0_0_6px_#ff3b3b]",
  warning: "bg-cyber-amber shadow-[0_0_6px_#ffb300]",
  info: "bg-[#00ff9c] shadow-[0_0_6px_#00ff9c]",
}

const TEXT: Record<AlertSeverity, string> = {
  critical: "text-[#ff3b3b]",
  warning: "text-cyber-amber",
  info: "text-[#00ff9c]",
}

/** Recent-alerts feed (right column of the mockup). */
const AlertList = ({ alerts, maxHeight = 240, onAcknowledge }: Props) => {
  if (alerts.length === 0) {
    return (
      <p className="py-4 text-center text-[0.7rem] uppercase tracking-widest text-cyber-orange/40">
        no active alerts
      </p>
    )
  }

  return (
    <div className="overflow-y-auto pr-1" style={{ maxHeight }}>
      {alerts.map((a) => (
        <button
          key={a.id}
          onClick={() => onAcknowledge?.(a.id)}
          className={`flex w-full items-center gap-2 border-b border-cyber-orange/10 py-1.5 text-left text-[0.7rem] transition-colors hover:bg-cyber-orange/5 ${
            a.acknowledged ? "opacity-40" : ""
          }`}
        >
          <span className="tabular-nums text-cyber-orange/60">
            {formatClock(new Date(a.timestamp))}
          </span>
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOT[a.severity]}`} />
          <span className={`flex-1 truncate uppercase tracking-wide ${TEXT[a.severity]}`}>
            {a.message}
          </span>
          {a.location && (
            <span className="text-cyber-orange/50">{a.location}</span>
          )}
        </button>
      ))}
    </div>
  )
}

export default AlertList
