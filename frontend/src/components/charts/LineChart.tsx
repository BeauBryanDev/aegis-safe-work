import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts"

const data = [
  { time: 0, value: 0.1 },
  { time: 1, value: 0.5 },
]

const FallChart = () => {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <XAxis dataKey="time" stroke="#ff6a00" />
        <YAxis stroke="#ff6a00" />
        <Tooltip />
        <Line type="monotone" dataKey="value" stroke="#ffb300" />
      </LineChart>
    </ResponsiveContainer>
  )
}

export default FallChart