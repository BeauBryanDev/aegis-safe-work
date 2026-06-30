import { LayoutDashboard, BarChart3, Bell, ScrollText, Settings } from "lucide-react"
import { ReactNode } from "react"

export interface NavItem {
  path: string
  label: string
  sublabel: string
  icon: ReactNode
}

/** Single source of truth for nav — must stay in sync with routes.tsx. */
export const NAV_ITEMS: NavItem[] = [
  { path: "/", label: "Dashboard", sublabel: "Overview", icon: <LayoutDashboard size={18} /> },
  { path: "/metrics", label: "Metrics", sublabel: "KPI & Analytics", icon: <BarChart3 size={18} /> },
  { path: "/alerts", label: "Alerts", sublabel: "Notifications", icon: <Bell size={18} /> },
  { path: "/logs", label: "Logs", sublabel: "Events & Logs", icon: <ScrollText size={18} /> },
  { path: "/settings", label: "Settings", sublabel: "Configuration", icon: <Settings size={18} /> },
]
