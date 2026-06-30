import Card from "../ui/Card"
import LiveStreamCanvas from "./LiveStreamCanvas"
import FPSCounter from "./FPSCounter"
import { useInference } from "../../hooks/useInference"
import { useDetectionStore } from "../../stores/useDetectionStore"

/**
 * Live-stream stage: camera feed + bounding-box overlay, with the HUD header
 * (camera id / resolution / FPS / LIVE) and the PEOPLE COUNT + PPE SCORE
 * readouts from the mockup.
 */
const LiveStreamPanel = () => {
  const { detections } = useInference()
  const peopleCount = useDetectionStore((s) => s.peopleCount)
  const ppe = useDetectionStore((s) => s.ppeCompliance)

  return (
    <Card
      title="Live Stream · CAM_01 — Production Line A"
      status={
        <span className="flex items-center gap-3">
          <FPSCounter />
          <span className="flex items-center gap-1 text-[#ff3b3b]">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#ff3b3b]" />
            LIVE
          </span>
        </span>
      }
      scanlines
    >
      <div className="relative">
        <LiveStreamCanvas detections={detections} />

        {/* corner readouts */}
        <div className="pointer-events-none absolute bottom-2 left-2 rounded border border-cyber-orange/50 bg-black/70 px-2 py-1">
          <span className="text-[0.55rem] uppercase tracking-widest text-cyber-orange/70">
            People Count
          </span>
          <div className="text-xl font-bold tabular-nums text-cyber-orange text-glow">
            {peopleCount}
          </div>
        </div>

        <div className="pointer-events-none absolute bottom-2 right-2 rounded border border-cyber-orange/50 bg-black/70 px-2 py-1 text-right">
          <span className="text-[0.55rem] uppercase tracking-widest text-cyber-orange/70">
            PPE Score
          </span>
          <div className="text-xl font-bold tabular-nums text-[#00ff9c] [text-shadow:0_0_8px_#00ff9c]">
            {ppe}%
          </div>
        </div>
      </div>
    </Card>
  )
}

export default LiveStreamPanel
