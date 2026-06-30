import { BarChart, Bar, ResponsiveContainer, Cell } from "recharts"

interface Props {
  data: number[]
  height?: number
  color?: string
}

/**
 * Tiny axis-less bar sparkline used inside KPI tiles (the little orange bars
 * under "PEOPLE COUNT", "FIRE/SMOKE ALERTS", etc. in the mockup).
 */
const Sparkline = ({ data, height = 32, color = "#ff6a00" }: Props) => {
  const chartData = data.map((value, i) => ({ i, value }))
  const max = Math.max(...data, 1)

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
        <Bar dataKey="value" isAnimationActive={false}>
          {chartData.map((d) => (
            <Cell
              key={d.i}
              fill={color}
              fillOpacity={0.35 + 0.65 * (d.value / max)}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export default Sparkline
