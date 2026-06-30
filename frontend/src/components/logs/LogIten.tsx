import { SystemLogEntry, LogLevel } from "../../types/metrics.types"
import { formatClock } from "../../hooks/useClock"

interface Props {
  log: SystemLogEntry
}

const LEVEL_TONE: Record<LogLevel, string> = {
  INFO: "text-[#00ff9c] border-[#00ff9c]/50",
  WARN: "text-cyber-amber border-cyber-amber/50",
  ERROR: "text-[#ff3b3b] border-[#ff3b3b]/50",
}

/**
 * Single system-log row (timestamp · level chip · source · message).
 * NOTE: filename is "LogIten" (pre-existing typo for LogItem).
 */
const LogItem = ({ log }: Props) => {
  return (
    <div className="flex items-center gap-2 border-b border-cyber-orange/10 py-1 text-[0.7rem]">
      <span className="tabular-nums text-cyber-orange/60">
        {formatClock(new Date(log.timestamp))}
      </span>
      <span
        className={`rounded border px-1 text-[0.55rem] uppercase tracking-widest ${LEVEL_TONE[log.level]}`}
      >
        {log.level}
      </span>
      <span className="text-cyber-amber/80">{log.source}</span>
      <span className="truncate text-cyber-orange/80">{log.message}</span>
    </div>
  )
}

export default LogItem
