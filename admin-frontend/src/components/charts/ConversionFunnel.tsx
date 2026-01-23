import { Card, Typography, Progress } from 'antd'
import { ArrowDownOutlined } from '@ant-design/icons'

interface FunnelStage {
  name: string
  name_ru: string
  value: number
  conversion_from_prev: number | null
  dropoff_count: number | null
  dropoff_percent: number | null
}

interface ConversionFunnelProps {
  stages: FunnelStage[]
  loading?: boolean
}

const STAGE_COLORS = [
  '#1890ff',
  '#52c41a',
  '#faad14',
  '#f5222d',
  '#722ed1',
  '#13c2c2',
]

export function ConversionFunnel({ stages, loading = false }: ConversionFunnelProps) {
  const maxValue = stages[0]?.value || 1

  return (
    <Card title="Воронка конверсии" loading={loading}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {stages.map((stage, idx) => {
          const widthPercent = (stage.value / maxValue) * 100
          const color = STAGE_COLORS[idx % STAGE_COLORS.length]

          return (
            <div key={stage.name}>
              {/* Stage row */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
                <div style={{ flex: 1 }}>
                  <Progress
                    percent={widthPercent}
                    showInfo={false}
                    strokeColor={color}
                    trailColor="#f0f0f0"
                    size="small"
                  />
                </div>
                <div style={{ minWidth: 150, textAlign: 'right' }}>
                  <Typography.Text strong>{stage.value.toLocaleString()}</Typography.Text>
                  {stage.conversion_from_prev !== null && (
                    <Typography.Text type="success" style={{ marginLeft: 8 }}>
                      {stage.conversion_from_prev.toFixed(1)}%
                    </Typography.Text>
                  )}
                </div>
              </div>

              {/* Stage name */}
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {stage.name_ru}
              </Typography.Text>

              {/* Drop-off indicator */}
              {stage.dropoff_count !== null && stage.dropoff_count > 0 && (
                <div style={{ marginTop: 4, marginBottom: 8 }}>
                  <Typography.Text type="danger" style={{ fontSize: 11 }}>
                    <ArrowDownOutlined /> -{stage.dropoff_percent?.toFixed(1)}%
                    ({stage.dropoff_count.toLocaleString()} users)
                  </Typography.Text>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
