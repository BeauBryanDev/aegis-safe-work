import { ButtonHTMLAttributes, ReactNode } from "react"

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode
  variant?: "solid" | "outline"
}

const CyberOrangeButton = ({
  children,
  variant = "outline",
  className = "",
  ...rest
}: Props) => {
  const base =
    "inline-flex items-center justify-center gap-2 rounded px-3 py-1.5 text-[0.7rem] uppercase tracking-[0.15em] transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed"

  const styles =
    variant === "solid"
      ? "bg-cyber-orange text-black shadow-[0_0_10px_rgba(255,106,0,0.6)] hover:bg-cyber-amber"
      : "border border-cyber-orange/60 text-cyber-orange hover:bg-cyber-orange/10 hover:shadow-[0_0_10px_rgba(255,106,0,0.5)]"

  return (
    <button className={`${base} ${styles} ${className}`} {...rest}>
      {children}
    </button>
  )
}

export default CyberOrangeButton
