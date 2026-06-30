import Card from "../components/ui/Card"
import LiveStreamPanel from "../components/videoStream/LiveStreamPanel"
import PeopleCountCard from "../components/KPI/PeopleCountCard"
import PPEComplianceCard from "../components/KPI/PPEComplianceCard"
import FireAlertCard from "../components/KPI/FireAlertCard"
import FailDetectionCard from "../components/KPI/FailDetectionCard"
import SystemLoadCard from "../components/KPI/SystemLoadCard"
import FallProbabilityChart from "../components/charts/LineChart"
import Histogram from "../components/charts/Histogram"
import HeatMap from "../components/charts/HeatMap"
import AlertList from "../components/alerts/AlertList"
import { useChartSeries } from "../hooks/useChartSeries"
import { useAlertStore } from "../stores/useAlertStore"

const Dashboard = () => {
  const { fallSeries, histogram } = useChartSeries()
  const alerts = useAlertStore((s) => s.alerts)
  const acknowledge = useAlertStore((s) => s.acknowledge)

  return (
    <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1fr_320px]">
      {/* main column */}
      <div className="flex flex-col gap-3">
        <LiveStreamPanel />

        <Card title="Fall Detection Probability Over Time" status="WINDOW: 32 · STEP: 8">
          <FallProbabilityChart data={fallSeries} />
        </Card>

        <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
          <Card title="Temporal Attention Map">
            <HeatMap />
          </Card>
          <Card title="Probability Distribution">
            <Histogram data={histogram} height={180} />
          </Card>
        </div>
      </div>

      {/* right KPI rail */}
      <div className="flex flex-col gap-3">
        <PeopleCountCard />
        <PPEComplianceCard />
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
          <FireAlertCard />
          <FailDetectionCard />
        </div>
        <SystemLoadCard />
        <Card title="Recent Alerts">
          <AlertList alerts={alerts.slice(0, 12)} maxHeight={220} onAcknowledge={acknowledge} />
        </Card>
      </div>
    </div>
  )
}

export default Dashboard
