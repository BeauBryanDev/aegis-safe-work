interface Props {
  /** size in px */
  size?: number
  active?: boolean
  className?: string
}

/**
 * Decorative pulsing orange core — the "reactor" glow used as an idle/active
 * indicator in the HUD.
 */
const OrangeGlowAnimation = ({ size = 14, active = true, className = "" }: Props) => (
  <span
    className={`relative inline-flex ${className}`}
    style={{ width: size, height: size }}
  >
    {active && (
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-cyber-orange opacity-60" />
    )}
    <span
      className="relative inline-flex rounded-full bg-cyber-orange shadow-[0_0_8px_#ff6a00,0_0_16px_#ff6a00]"
      style={{ width: size, height: size }}
    />
  </span>
)

export default OrangeGlowAnimation
