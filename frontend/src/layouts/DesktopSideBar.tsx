import { NavLink } from "react-router-dom"
import { NAV_ITEMS } from "./navItems"
import { useDetectionStore } from "../stores/useDetectionStore"
import OrangeGlowAnimation from "../components/ui/OrangeGlowAnimation"

const MODELS = [
  { name: "Fire/Smoke Detector", tag: "YOLOv8n (ONNX.JS)", active: true },
  { name: "PPE Detector", tag: "YOLOv11s (backend)", active: false },
  { name: "Human Fall Detector", tag: "EffNet+MLP (backend)", active: false },
]

/** Left icon+label sidebar nav (desktop) + AI model status panel. */
const DesktopSideBar = () => {
  const compliance = useDetectionStore((s) => s.ppeCompliance)

  return (
    <aside className="hidden w-60 shrink-0 flex-col gap-3 overflow-y-auto border-r border-cyber-orange/30 bg-black/40 p-3 md:flex">
      <nav className="flex flex-col gap-1">
        <span className="mb-1 text-[0.6rem] uppercase tracking-[0.2em] text-cyber-orange/50">
          // Navigation
        </span>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded border px-3 py-2 transition-all ${
                isActive
                  ? "border-cyber-orange/70 bg-cyber-orange/10 text-cyber-orange shadow-[0_0_8px_rgba(255,106,0,0.4)]"
                  : "border-transparent text-cyber-orange/50 hover:text-cyber-orange"
              }`
            }
          >
            {item.icon}
            <span className="leading-tight">
              <span className="block text-xs uppercase tracking-widest">{item.label}</span>
              <span className="block text-[0.55rem] uppercase tracking-wider opacity-60">
                {item.sublabel}
              </span>
            </span>
          </NavLink>
        ))}
      </nav>

      {/* AI models status */}
      <div className="mt-2 rounded border border-cyber-orange/30 p-2">
        <span className="text-[0.6rem] uppercase tracking-[0.2em] text-cyber-orange/50">
          // AI Models Status
        </span>
        <ul className="mt-2 space-y-2">
          {MODELS.map((m) => (
            <li key={m.name} className="flex items-center justify-between gap-2">
              <span className="leading-tight">
                <span className="block text-[0.65rem] uppercase tracking-wide text-cyber-orange/90">
                  {m.name}
                </span>
                <span className="block text-[0.5rem] uppercase tracking-wider text-cyber-amber/60">
                  {m.tag}
                </span>
              </span>
              <span className="flex items-center gap-1 text-[0.55rem] uppercase tracking-widest">
                <OrangeGlowAnimation size={6} active={m.active} />
                <span className={m.active ? "text-[#00ff9c]" : "text-cyber-orange/40"}>
                  {m.active ? "Active" : "Standby"}
                </span>
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* environment readout */}
      <div className="rounded border border-cyber-orange/30 p-2 text-[0.6rem] uppercase tracking-widest text-cyber-orange/70">
        <span className="text-cyber-orange/50">// Environment</span>
        <div className="mt-1 flex justify-between">
          <span>Temp 32.4°C</span>
          <span>Hum 48.7%</span>
        </div>
        <div className="mt-1 flex justify-between">
          <span>Air: <span className="text-[#00ff9c]">Good</span></span>
          <span>PPE {compliance}%</span>
        </div>
      </div>
    </aside>
  )
}

export default DesktopSideBar
