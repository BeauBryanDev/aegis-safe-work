import LiveStreamCanvas from "../components/video/LiveStreamCanvas"
import { useInference } from "../hooks/useInference"

const Dashboard = () => {
  const { detections } = useInference()

  return (
    <div className="p-2">
      <LiveStreamCanvas detections={detections} />
    </div>
  )
}

export default Dashboard