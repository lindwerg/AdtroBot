import { Card, Statistic, Typography } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons'
import { AreaChart, Area, ResponsiveContainer, XAxis } from 'recharts'

interface SparklinePoint {
  date: string
  value: number
}

interface KPICardProps {
  title: string
  value: number | string
  trend: number
  sparkline?: SparklinePoint[]
  prefix?: string
  suffix?: string
  invertTrend?: boolean  // true for metrics where decrease is good (errors)
  loading?: boolean
}

export function KPICard({
  title,
  value,
  trend,
  sparkline = [],
  prefix,
  suffix,
  invertTrend = false,
  loading = false,
}: KPICardProps) {
  const isPositive = invertTrend ? trend < 0 : trend > 0
  const trendColor = trend === 0 ? '#8c8c8c' : isPositive ? '#3f8600' : '#cf1322'
  const chartColor = isPositive ? '#3f8600' : '#cf1322'

  return (
    <Card size="small" loading={loading} style={{ height: '100%' }}>
      <Statistic
        title={title}
        value={value}
        prefix={prefix}
        suffix={suffix}
        valueStyle={{ fontSize: 24 }}
      />
      {trend !== 0 && (
        <Typography.Text style={{ color: trendColor, fontSize: 12 }}>
          {isPositive ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
          {' '}{Math.abs(trend).toFixed(1)}%
          <span style={{ color: '#8c8c8c', marginLeft: 4 }}>vs вчера</span>
        </Typography.Text>
      )}
      {sparkline.length > 0 && (
        <div style={{ marginTop: 8, height: 40 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sparkline}>
              <XAxis dataKey="date" hide />
              <Area
                type="monotone"
                dataKey="value"
                stroke={chartColor}
                fill={chartColor}
                fillOpacity={0.1}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </Card>
  )
}
