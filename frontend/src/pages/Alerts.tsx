import Card from "../components/ui/Card"
import Badge from "../components/ui/Badge"
import CyberOrangeButton from "../components/ui/CyberOrangeButton"
import AlertList from "../components/alerts/AlertList"
import { useAlertStore, selectUnacknowledged } from "../stores/useAlertStore"

const Alerts = () => {
  const alerts = useAlertStore((s) => s.alerts)
  const acknowledge = useAlertStore((s) => s.acknowledge)
  const acknowledgeAll = useAlertStore((s) => s.acknowledgeAll)
  const clear = useAlertStore((s) => s.clear)
  const unacked = useAlertStore(selectUnacknowledged)

  return (
    <Card
      title="Location Alerts & Notifications"
      status={
        <Badge tone={unacked ? "red" : "green"} pulse={unacked > 0}>
          {unacked} unacknowledged
        </Badge>
      }
    >
      <div className="mb-3 flex gap-2">
        <CyberOrangeButton onClick={acknowledgeAll} disabled={!unacked}>
          Acknowledge All
        </CyberOrangeButton>
        <CyberOrangeButton onClick={clear} disabled={!alerts.length}>
          Clear
        </CyberOrangeButton>
      </div>

      <AlertList alerts={alerts} maxHeight={520} onAcknowledge={acknowledge} />
    </Card>
  )
}

export default Alerts
