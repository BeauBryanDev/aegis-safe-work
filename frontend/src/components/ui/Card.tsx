import { ReactNode } from "react"

interface CardProps {
  title?: string
  /** small right-aligned status text in the title bar, e.g. "● LIVE" */
  status?: ReactNode
  children: ReactNode
  className?: string
  /** add the animated scanline texture overlay */
  scanlines?: boolean
}

/**
 * The signature bracket-corner HUD panel. Base container for every widget.
 * Renders four glowing corner brackets + an optional uppercase title bar.
 */
const Corner = ({ className }: { className: string }) => (
  <span
    aria-hidden
    className={`pointer-events-none absolute h-3 w-3 border-cyber-orange ${className}`}
  />
)

const Card = ({ title, status, children, className = "", scanlines }: CardProps) => {
  return (
    <div
      className={`relative rounded-md border border-cyber-orange/40 bg-gradient-to-br from-cyber-orange/5 to-black/90 p-3 shadow-[0_0_8px_rgba(255,106,0,0.35)] ${
        scanlines ? "scanlines" : ""
      } ${className}`}
    >
      <Corner className="left-0 top-0 border-l border-t" />
      <Corner className="right-0 top-0 border-r border-t" />
      <Corner className="bottom-0 left-0 border-b border-l" />
      <Corner className="bottom-0 right-0 border-b border-r" />

      {(title || status) && (
        <div className="mb-2 flex items-center justify-between border-b border-cyber-orange/30 pb-1">
          {title && (
            <h2 className="text-[0.7rem] uppercase tracking-[0.18em] text-cyber-orange/90">
              {title}
            </h2>
          )}
          {status && (
            <span className="text-[0.65rem] uppercase tracking-widest text-cyber-amber">
              {status}
            </span>
          )}
        </div>
      )}

      {children}
    </div>
  )
}

export default Card
