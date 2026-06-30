import { SystemLogEntry } from "../../types/metrics.types"
import LogItem from "./LogIten"

interface Props {
  logs: SystemLogEntry[]
  maxHeight?: number
}

/** Scrollable system-logs / events panel (newest first). */
const SystemLogs = ({ logs, maxHeight = 240 }: Props) => {
  if (logs.length === 0) {
    return (
      <p className="py-4 text-center text-[0.7rem] uppercase tracking-widest text-cyber-orange/40">
        no log entries
      </p>
    )
  }

  return (
    <div className="overflow-y-auto pr-1" style={{ maxHeight }}>
      {logs.map((log) => (
        <LogItem key={log.id} log={log} />
      ))}
    </div>
  )
}

export default SystemLogs
