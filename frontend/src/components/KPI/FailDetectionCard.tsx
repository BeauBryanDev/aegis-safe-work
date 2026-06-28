import { PersonStanding } from "lucide-react"
import KPICard from "./KPICard"
import { useDetectionStore } from "../../stores/useDetectionStore"

/** Fall ("fail") detection KPI — count of detected falls. */
const FailDetectionCard = () => {
  const fallCount = useDetectionStore((s) => s.fallCount)
  const fallDetected = useDetectionStore((s) => s.fallDetected)

  return (
    <KPICard
      label="Fall Detections"
      value={fallCount}
      tone={fallDetected ? "red" : "orange"}
      alert={fallDetected}
      icon={<PersonStanding size={16} />}
      footer={
        <span className="text-[0.6rem] uppercase tracking-widest text-cyber-orange/50">
          {fallDetected ? "⚠ worker down" : "effnet+mlp (backend)"}
        </span>
      }
    />
  )
}

export default FailDetectionCard
