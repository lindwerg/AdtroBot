import { Row, Col, Typography, Segmented, Space, Alert, Button, Spin } from 'antd'
import { ExportOutlined, ReloadOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { KPICard, ConversionFunnel } from '@/components/charts'
import { useDashboardMetrics, useFunnelData } from '@/hooks/useDashboard'

export default function Dashboard() {
  const [funnelPeriod, setFunnelPeriod] = useState<number>(30)

  const { data: metrics, isLoading: metricsLoading, error: metricsError, refetch: refetchMetrics } = useDashboardMetrics()
  const { data: funnel, isLoading: funnelLoading, refetch: refetchFunnel } = useFunnelData(funnelPeriod)

  const isInitialLoading = metricsLoading && !metrics

  if (metricsError) {
    return (
      <Alert
        type="error"
        message="Ошибка загрузки данных"
        description="Не удалось загрузить метрики dashboard. Проверьте подключение к серверу."
        showIcon
        action={
          <Button size="small" icon={<ReloadOutlined />} onClick={() => refetchMetrics()}>
            Повторить
          </Button>
        }
      />
    )
  }

  const handleRefresh = () => {
    refetchMetrics()
    refetchFunnel()
  }

  return (
    <Spin spinning={isInitialLoading} tip="Загрузка метрик...">
      <div>
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Typography.Title level={4} style={{ margin: 0 }}>Dashboard</Typography.Title>
          </Col>
          <Col>
            <Button
              icon={<ReloadOutlined spin={metricsLoading && !!metrics} />}
              onClick={handleRefresh}
              disabled={metricsLoading}
            >
              Обновить
            </Button>
          </Col>
        </Row>

      {/* Growth & Activity */}
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        Рост и активность
      </Typography.Text>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="DAU"
            value={metrics?.active_users_dau.value ?? 0}
            trend={metrics?.active_users_dau.trend ?? 0}
            sparkline={metrics?.active_users_dau.sparkline}
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="MAU"
            value={metrics?.active_users_mau.value ?? 0}
            trend={metrics?.active_users_mau.trend ?? 0}
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Новых сегодня"
            value={metrics?.new_users_today.value ?? 0}
            trend={metrics?.new_users_today.trend ?? 0}
            sparkline={metrics?.new_users_today.sparkline}
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Retention D7"
            value={metrics?.retention_d7.value ?? '0%'}
            trend={metrics?.retention_d7.trend ?? 0}
            loading={metricsLoading}
          />
        </Col>
      </Row>

      {/* Product Metrics */}
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        Продуктовые метрики
      </Typography.Text>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Таро раскладов"
            value={metrics?.tarot_spreads_today.value ?? 0}
            trend={metrics?.tarot_spreads_today.trend ?? 0}
            sparkline={metrics?.tarot_spreads_today.sparkline}
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Самый активный знак"
            value={metrics?.most_active_zodiac ?? 'N/A'}
            trend={0}
            loading={metricsLoading}
          />
        </Col>
      </Row>

      {/* Revenue */}
      <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        Доход
      </Typography.Text>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Доход сегодня"
            value={metrics?.revenue_today.value ?? 0}
            trend={metrics?.revenue_today.trend ?? 0}
            sparkline={metrics?.revenue_today.sparkline}
            suffix=" RUB"
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Доход за месяц"
            value={metrics?.revenue_month.value ?? 0}
            trend={metrics?.revenue_month.trend ?? 0}
            suffix=" RUB"
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="Конверсия"
            value={metrics?.conversion_rate.value ?? '0%'}
            trend={metrics?.conversion_rate.trend ?? 0}
            loading={metricsLoading}
          />
        </Col>
        <Col xs={12} sm={8} md={6}>
          <KPICard
            title="ARPU"
            value={metrics?.arpu.value ?? '0'}
            trend={metrics?.arpu.trend ?? 0}
            suffix=" RUB"
            loading={metricsLoading}
          />
        </Col>
      </Row>

      {/* Funnel */}
      <Space style={{ marginBottom: 16 }}>
        <Typography.Text>Период:</Typography.Text>
        <Segmented
          value={funnelPeriod}
          onChange={(v) => setFunnelPeriod(Number(v))}
          options={[
            { label: '7 дней', value: 7 },
            { label: '30 дней', value: 30 },
            { label: '90 дней', value: 90 },
          ]}
        />
        <Button
          icon={<ExportOutlined />}
          onClick={() => window.open(`/admin/export/metrics?days=${funnelPeriod}`, '_blank')}
        >
          Экспорт метрик
        </Button>
      </Space>
      <ConversionFunnel
        stages={funnel?.stages ?? []}
        loading={funnelLoading}
      />
      </div>
    </Spin>
  )
}
