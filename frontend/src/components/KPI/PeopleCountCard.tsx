import { Users } from "lucide-react"
import KPICard from "./KPICard"
import { useDetectionStore } from "../../stores/useDetectionStore"

const PeopleCountCard = () => {
  const peopleCount = useDetectionStore((s) => s.peopleCount)

  return (
    <KPICard
      label="People Count"
      value={peopleCount}
      tone="orange"
      icon={<Users size={16} />}
      footer={
        <span className="text-[0.6rem] uppercase tracking-widest text-cyber-orange/50">
          live in frame
        </span>
      }
    />
  )
}

export default PeopleCountCard
