import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts"

interface Props {
  /** 0–100 */
  value: number
  size?: number
  label?: string
}

const tone = (pct: number) =>
  pct >= 80 ? "#ff6a00" : pct >= 60 ? "#ffb300" : "#ff3b3b"

/**
 * Compliance donut gauge (the "80% COMPLIANT" ring in the mockup). Renders a
 * single percentage as a glowing partial ring with a centered readout.
 */
const ComplianceDonut = ({ value, size = 130, label = "COMPLIANT" }: Props) => {
  const color = tone(value)
  const data = [
    { name: "value", value },
    { name: "rest", value: 100 - value },
  ]

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            innerRadius="74%"
            outerRadius="100%"
            startAngle={90}
            endAngle={-270}
            stroke="none"
            isAnimationActive={false}
          >
            <Cell fill={color} />
            <Cell fill="#ff6a00" fillOpacity={0.08} />
          </Pie>
        </PieChart>
      </ResponsiveContainer>

      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <span
          className="text-2xl font-bold tabular-nums"
          style={{ color, textShadow: `0 0 8px ${color}` }}
        >
          {value}
          <span className="text-sm">%</span>
        </span>
        <span className="text-[0.55rem] uppercase tracking-widest text-cyber-orange/60">
          {label}
        </span>
      </div>
    </div>
  )
}

export default ComplianceDonut
