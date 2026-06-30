import { Menu } from "lucide-react"
import DateCard from "../components/ui/DateCard"
import aegisIcon from "../assets/aegis_icon.webp"
import { useUIStore } from "../stores/useUIStore"
import { useAppStore } from "../stores/useAppStore"

/** Top status bar: wordmark · title · system status · clock. */
const Header = () => {
  const setMobileMenu = useUIStore((s) => s.setMobileMenu)
  const mobileMenuOpen = useUIStore((s) => s.mobileMenuOpen)
  const status = useAppStore((s) => s.systemStatus)

  return (
    <header className="flex items-center justify-between border-b border-cyber-orange/40 bg-black/60 px-4 py-2 shadow-[0_0_8px_rgba(255,106,0,0.3)]">
      {/* wordmark */}
      <div className="flex items-center gap-2">
        <img
          src={aegisIcon}
          alt="Aegis Safe-Work"
          className="h-9 w-9 object-contain drop-shadow-[0_0_8px_rgba(255,106,0,0.6)]"
        />
        <div className="leading-tight">
          <h1 className="text-lg font-bold uppercase tracking-[0.15em] text-cyber-orange text-glow">
            Aegis Safe-Work
          </h1>
          <p className="hidden text-[0.55rem] uppercase tracking-[0.2em] text-cyber-amber/70 sm:block">
            PPE Compliance &amp; Fall Detection System
          </p>
        </div>
      </div>

      {/* center title (desktop only) */}
      <div className="hidden flex-col items-center lg:flex">
        <span className="text-sm uppercase tracking-[0.25em] text-cyber-orange/90">
          Cyberpunk Vision Console
        </span>
        <span className="text-[0.55rem] uppercase tracking-[0.2em] text-cyber-amber/60">
          Real-Time Industrial Safety Monitoring
        </span>
      </div>

      {/* right: status + clock + mobile menu */}
      <div className="flex items-center gap-4">
        <div className="hidden flex-col items-end leading-tight md:flex">
          <span className="text-[0.55rem] uppercase tracking-widest text-cyber-amber/60">
            System Status
          </span>
          <span className="text-xs uppercase tracking-widest text-[#00ff9c] [text-shadow:0_0_6px_#00ff9c]">
            {status}
          </span>
        </div>
        <DateCard />
        <button
          aria-label="Toggle menu"
          onClick={() => setMobileMenu(!mobileMenuOpen)}
          className="text-cyber-orange md:hidden"
        >
          <Menu size={24} />
        </button>
      </div>
    </header>
  )
}

export default Header
