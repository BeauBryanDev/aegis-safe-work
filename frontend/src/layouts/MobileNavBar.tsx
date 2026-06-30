import { NavLink } from "react-router-dom"
import { NAV_ITEMS } from "./navItems"

/** Bottom tab bar (mobile). Hidden on desktop. */
const MobileNavBar = () => {
  return (
    <nav className="fixed bottom-0 left-0 z-40 flex w-full justify-around border-t border-cyber-orange/50 bg-black/90 py-2 shadow-[0_0_10px_rgba(255,106,0,0.4)] md:hidden">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.path === "/"}
          className={({ isActive }) =>
            `flex flex-col items-center gap-1 px-2 text-[0.55rem] uppercase tracking-widest transition-colors ${
              isActive
                ? "text-cyber-orange [text-shadow:0_0_6px_#ff6a00]"
                : "text-cyber-orange/45"
            }`
          }
        >
          {item.icon}
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}

export default MobileNavBar
