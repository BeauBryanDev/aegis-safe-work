import Card from "../components/ui/Card"
import FallProbabilityChart from "../components/charts/LineChart"
import Histogram from "../components/charts/Histogram"
import HeatMap from "../components/charts/HeatMap"
import ComplianceDonut from "../components/charts/PieChart"
import PPEComplianceCard from "../components/KPI/PPEComplianceCard"
import { useChartSeries } from "../hooks/useChartSeries"
import { useDetectionStore } from "../stores/useDetectionStore"

const Metrics = () => {
  const { fallSeries, histogram } = useChartSeries()
  const compliance = useDetectionStore((s) => s.ppeCompliance)

  return (
    <div className="flex flex-col gap-3">
      <Card title="Fall Detection Probability Over Time" status="WINDOW: 32 · STEP: 8">
        <FallProbabilityChart data={fallSeries} height={240} />
      </Card>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <Card title="Probability Distribution">
          <Histogram data={histogram} height={220} />
        </Card>
        <Card title="Temporal Attention Map">
          <HeatMap rows={10} cols={32} />
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[260px_1fr]">
        <Card title="PPE Compliance" className="flex items-center justify-center">
          <ComplianceDonut value={compliance} size={160} />
        </Card>
        <PPEComplianceCard />
      </div>
    </div>
  )
}

export default Metrics
