import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts"
import { TimePoint } from "../../types/metrics.types"

interface Props {
  data: TimePoint[]
  height?: number
  /** draw a dashed threshold line (e.g. fall-alert threshold) */
  threshold?: number
}

/**
 * Fall-detection-probability-over-time chart (the big center chart in the
 * mockup). Orange area + line on near-black, red dashed alert threshold.
 */
const FallProbabilityChart = ({ data, height = 200, threshold = 0.75 }: Props) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: -12, bottom: 0 }}>
        <defs>
          <linearGradient id="fallFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#ff6a00" stopOpacity={0.45} />
            <stop offset="100%" stopColor="#ff6a00" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#ff6a00" strokeOpacity={0.12} vertical={false} />
        <XAxis
          dataKey="time"
          stroke="#ffb300"
          tick={{ fill: "#ffb300", fontSize: 10 }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 1]}
          stroke="#ffb300"
          tick={{ fill: "#ffb300", fontSize: 10 }}
          tickLine={false}
          width={34}
        />
        <Tooltip
          contentStyle={{
            background: "#000",
            border: "1px solid #ff6a00",
            borderRadius: 4,
            fontSize: 11,
            textTransform: "uppercase",
          }}
          labelStyle={{ color: "#ffb300" }}
          itemStyle={{ color: "#ff6a00" }}
        />
        <ReferenceLine
          y={threshold}
          stroke="#ff3b3b"
          strokeDasharray="4 4"
          strokeOpacity={0.7}
        />
        <Area
          type="monotone"
          dataKey="value"
          stroke="#ff6a00"
          strokeWidth={1.5}
          fill="url(#fallFill)"
          isAnimationActive={false}
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export default FallProbabilityChart
