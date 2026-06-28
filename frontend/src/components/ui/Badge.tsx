import { ReactNode } from "react"

export type BadgeTone = "orange" | "amber" | "green" | "red" | "muted"

const TONES: Record<BadgeTone, string> = {
  orange: "text-cyber-orange border-cyber-orange/60",
  amber: "text-cyber-amber border-cyber-amber/60",
  green: "text-[#00ff9c] border-[#00ff9c]/60",
  red: "text-[#ff3b3b] border-[#ff3b3b]/60",
  muted: "text-cyber-orange/50 border-cyber-orange/20",
}

interface BadgeProps {
  children: ReactNode
  tone?: BadgeTone
  pulse?: boolean
  className?: string
}

const Badge = ({ children, tone = "orange", pulse, className = "" }: BadgeProps) => (
  <span
    className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[0.6rem] uppercase tracking-widest ${
      TONES[tone]
    } ${pulse ? "pulse" : ""} ${className}`}
  >
    {children}
  </span>
)

export default Badge
