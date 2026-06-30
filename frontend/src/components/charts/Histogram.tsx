import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts"
import { HistogramBin } from "../../types/metrics.types"

interface Props {
  data: HistogramBin[]
  height?: number
}

/**
 * Probability-distribution histogram (bottom-center of the mockup —
 * "WINDOWS COUNT vs FALL PROBABILITY"). Orange bars on near-black.
 */
const Histogram = ({ data, height = 200 }: Props) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="#ff6a00" strokeOpacity={0.1} vertical={false} />
        <XAxis
          dataKey="bin"
          stroke="#ffb300"
          tick={{ fill: "#ffb300", fontSize: 9 }}
          tickLine={false}
        />
        <YAxis
          stroke="#ffb300"
          tick={{ fill: "#ffb300", fontSize: 9 }}
          tickLine={false}
          width={34}
        />
        <Tooltip
          cursor={{ fill: "#ff6a00", fillOpacity: 0.08 }}
          contentStyle={{
            background: "#000",
            border: "1px solid #ff6a00",
            borderRadius: 4,
            fontSize: 11,
          }}
          labelStyle={{ color: "#ffb300" }}
          itemStyle={{ color: "#ff6a00" }}
        />
        <Bar
          dataKey="count"
          fill="#ff6a00"
          fillOpacity={0.7}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default Histogram
