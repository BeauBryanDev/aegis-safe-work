import { useClock, formatClock, formatDate } from "../../hooks/useClock"

/** Compact date/time readout for the header (right side of the mockup). */
const DateCard = () => {
  const now = useClock()

  return (
    <div className="flex flex-col items-end leading-tight">
      <span className="text-sm font-bold tabular-nums text-cyber-orange text-glow">
        {formatClock(now)}
      </span>
      <span className="text-[0.6rem] uppercase tracking-widest text-cyber-amber/80">
        {formatDate(now)}
      </span>
    </div>
  )
}

export default DateCard
