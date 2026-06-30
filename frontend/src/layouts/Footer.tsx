import { useAppStore } from "../stores/useAppStore"

const formatUptime = (s: number) => {
  const hh = String(Math.floor(s / 3600)).padStart(2, "0")
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0")
  const ss = String(s % 60).padStart(2, "0")
  return `${hh}:${mm}:${ss}`
}

/** Bottom system-info bar (desktop). Mirrors the mockup footer strip. */
const Footer = () => {
  const metrics = useAppStore((s) => s.metrics)

  return (
    <footer className="hidden items-center justify-between border-t border-cyber-orange/40 bg-black/60 px-4 py-1.5 text-[0.6rem] uppercase tracking-widest text-cyber-orange/60 md:flex">
      <span>
        Aegis Safe-Work v0.1.0 · Build 2027.05 · <span className="text-[#00ff9c]">Active</span>
      </span>
      <span className="hidden lg:inline">
        AI Engine: ONNX.JS Runtime · WebGPU · Inference {metrics.fps || "—"} FPS
      </span>
      <span>
        Load {metrics.systemLoad}% · Ping {metrics.latencyMs}ms · Uptime{" "}
        <span className="tabular-nums text-cyber-amber">
          {formatUptime(metrics.uptimeSeconds)}
        </span>
      </span>
    </footer>
  )
}

export default Footer
