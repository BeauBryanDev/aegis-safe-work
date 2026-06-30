import { useFPS } from "../../hooks/useFPS"

interface Props {
  /** override the measured value (e.g. inference FPS from the backend) */
  value?: number
  className?: string
}

/** Small "FPS: 24.7" readout overlaid on the live-stream header. */
const FPSCounter = ({ value, className = "" }: Props) => {
  const measured = useFPS(value === undefined)
  const fps = value ?? measured

  return (
    <span
      className={`font-mono text-[0.65rem] uppercase tracking-widest text-cyber-amber ${className}`}
    >
      FPS: <span className="tabular-nums text-cyber-orange">{fps.toFixed(1)}</span>
    </span>
  )
}

export default FPSCounter
