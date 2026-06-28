import { Flame } from "lucide-react"
import KPICard from "./KPICard"
import { useDetectionStore } from "../../stores/useDetectionStore"

const FireAlertCard = () => {
  const fireCount = useDetectionStore((s) => s.fireCount)
  const fireDetected = useDetectionStore((s) => s.fireDetected)

  return (
    <KPICard
      label="Fire / Smoke Alerts"
      value={fireCount}
      tone={fireDetected ? "red" : "orange"}
      alert={fireDetected}
      icon={<Flame size={16} />}
      footer={
        <span className="text-[0.6rem] uppercase tracking-widest text-cyber-orange/50">
          {fireDetected ? "⚠ active signature" : "client-side yolov8n"}
        </span>
      }
    />
  )
}

export default FireAlertCard
