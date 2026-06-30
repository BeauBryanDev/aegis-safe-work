import { useEffect, useState } from "react"
import Card from "../components/ui/Card"
import Badge from "../components/ui/Badge"
import SystemLogs from "../components/logs/SystemLogs"
import { seedLogs, genAlert } from "../services/mockData"
import { SystemLogEntry } from "../types/metrics.types"

/** System logs page — seeded mock feed that grows over time. */
const Logs = () => {
  const [logs, setLogs] = useState<SystemLogEntry[]>(() => seedLogs(30))

  useEffect(() => {
    const id = setInterval(() => {
      // reuse the alert generator's randomness to fabricate a log line
      const a = genAlert()
      setLogs((prev) =>
        [
          {
            id: a.id,
            level: a.severity === "critical" ? "ERROR" : a.severity === "warning" ? "WARN" : "INFO",
            source: "vision.core",
            message: a.message,
            timestamp: a.timestamp,
          } as SystemLogEntry,
          ...prev,
        ].slice(0, 200)
      )
    }, 4000)
    return () => clearInterval(id)
  }, [])

  return (
    <Card
      title="System Logs · Events"
      status={<Badge tone="muted">{logs.length} entries</Badge>}
    >
      <SystemLogs logs={logs} maxHeight={560} />
    </Card>
  )
}

export default Logs
