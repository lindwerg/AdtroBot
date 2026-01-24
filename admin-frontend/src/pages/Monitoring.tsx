import { useState } from 'react'
import {
  Row,
  Col,
  Card,
  Typography,
  Segmented,
  Statistic,
  Table,
  Alert,
  Spin,
  Button,
  Space,
} from 'antd'
import {
  UserOutlined,
  DollarOutlined,
  ApiOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'
import { useMonitoringData } from '@/hooks/useMonitoring'
import type { TimeRange, CostByOperation } from '@/api/monitoring'

const { Title, Text } = Typography

// Operation name translations
const operationNames: Record<string, string> = {
  horoscope: 'Гороскоп',
  tarot: 'Таро (3 карты)',
  celtic_cross: 'Кельтский крест',
  card_of_day: 'Карта дня',
  natal_interpretation: 'Натальная карта',
  detailed_natal: 'Детальная карта',
  premium_horoscope: 'Премиум гороскоп',
  unknown: 'Другое',
}

export default function Monitoring() {
  const [range, setRange] = useState<TimeRange>('7d')
  const { data, isLoading, error, refetch } = useMonitoringData(range)

  const isInitialLoading = isLoading && !data
  const hasNoData = !isLoading && data &&
    (data.api_costs?.total_requests === 0 || !data.api_costs?.by_day?.length)

  if (error) {
    return (
      <Alert
        type="error"
        message="Ошибка загрузки данных мониторинга"
        description="Не удалось получить данные мониторинга. Проверьте подключение к серверу."
        showIcon
        action={
          <Button size="small" icon={<ReloadOutlined />} onClick={() => refetch()}>
            Повторить
          </Button>
        }
      />
    )
  }

  const costColumns = [
    {
      title: 'Операция',
      dataIndex: 'operation',
      key: 'operation',
      render: (op: string) => operationNames[op] || op,
    },
    {
      title: 'Запросов',
      dataIndex: 'requests',
      key: 'requests',
      sorter: (a: CostByOperation, b: CostByOperation) => a.requests - b.requests,
    },
    {
      title: 'Токенов',
      dataIndex: 'tokens',
      key: 'tokens',
      render: (v: number) => v.toLocaleString(),
      sorter: (a: CostByOperation, b: CostByOperation) => a.tokens - b.tokens,
    },
    {
      title: 'Стоимость',
      dataIndex: 'cost',
      key: 'cost',
      render: (v: number) => `$${v.toFixed(4)}`,
      sorter: (a: CostByOperation, b: CostByOperation) => a.cost - b.cost,
    },
  ]

  // Calculate totals for display
  const totalCost = data?.api_costs?.total_cost ?? 0
  const totalTokens = data?.api_costs?.total_tokens ?? 0
  const costPerUser = data?.unit_economics?.cost_per_active_user ?? 0
  const costPerPayingUser = data?.unit_economics?.cost_per_paying_user ?? 0

  return (
    <Spin spinning={isInitialLoading} tip="Загрузка данных мониторинга...">
      <div>
        {/* Header with time filter */}
        <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
          <Col>
            <Title level={4} style={{ margin: 0 }}>Мониторинг</Title>
          </Col>
          <Col>
            <Space>
              <Segmented
                value={range}
                onChange={(v) => setRange(v as TimeRange)}
                options={[
                  { label: '24 часа', value: '24h' },
                  { label: '7 дней', value: '7d' },
                  { label: '30 дней', value: '30d' },
                ]}
                disabled={isLoading}
              />
              <Button
                icon={<ReloadOutlined spin={isLoading && !!data} />}
                onClick={() => refetch()}
                disabled={isLoading}
              >
                Обновить
              </Button>
            </Space>
          </Col>
        </Row>

        {/* Empty state for no data in period */}
        {hasNoData && (
          <Alert
            type="info"
            message="Нет данных за выбранный период"
            description="API запросы не выполнялись за выбранный временной диапазон. Попробуйте выбрать другой период."
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

      {/* Active Users Section */}
      <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        Активные пользователи
      </Text>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={8}>
          <Card loading={isLoading}>
            <Statistic
              title="DAU (сегодня)"
              value={data?.active_users?.dau ?? 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card loading={isLoading}>
            <Statistic
              title="WAU (7 дней)"
              value={data?.active_users?.wau ?? 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={8}>
          <Card loading={isLoading}>
            <Statistic
              title="MAU (30 дней)"
              value={data?.active_users?.mau ?? 0}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* API Costs Section */}
      <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        API Costs (OpenRouter)
      </Text>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Общая стоимость"
              value={totalCost}
              precision={4}
              prefix={<DollarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Всего токенов"
              value={totalTokens}
              prefix={<ApiOutlined />}
              formatter={(value) => Number(value).toLocaleString()}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Запросов"
              value={data?.api_costs?.total_requests ?? 0}
              prefix={<ThunderboltOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Средняя стоимость запроса"
              value={data?.api_costs?.total_requests ? totalCost / data.api_costs.total_requests : 0}
              precision={6}
              prefix="$"
            />
          </Card>
        </Col>
      </Row>

      {/* Cost Chart */}
      <Card title="Стоимость по дням" style={{ marginBottom: 24 }} loading={isLoading}>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={data?.api_costs?.by_day ?? []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="date"
              tickFormatter={(v) => {
                const d = new Date(v)
                return `${d.getDate()}.${d.getMonth() + 1}`
              }}
            />
            <YAxis tickFormatter={(v) => `$${v.toFixed(3)}`} />
            <Tooltip
              formatter={(value) => [`$${Number(value).toFixed(4)}`, 'Стоимость']}
              labelFormatter={(label) => {
                const d = new Date(label)
                return d.toLocaleDateString('ru-RU')
              }}
            />
            <Area
              type="monotone"
              dataKey="cost"
              stroke="#1890ff"
              fill="#1890ff"
              fillOpacity={0.3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      {/* Cost by Operation */}
      <Card title="Стоимость по операциям" style={{ marginBottom: 24 }} loading={isLoading}>
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Table
              dataSource={data?.api_costs?.by_operation ?? []}
              columns={costColumns}
              rowKey="operation"
              pagination={false}
              size="small"
            />
          </Col>
          <Col xs={24} md={12}>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data?.api_costs?.by_operation ?? []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(v) => `$${v.toFixed(3)}`} />
                <YAxis
                  type="category"
                  dataKey="operation"
                  width={100}
                  tickFormatter={(v) => operationNames[v] || v}
                />
                <Tooltip formatter={(value) => [`$${Number(value).toFixed(4)}`, 'Стоимость']} />
                <Bar dataKey="cost" fill="#52c41a" />
              </BarChart>
            </ResponsiveContainer>
          </Col>
        </Row>
      </Card>

      {/* Unit Economics */}
      <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
        Unit Economics
      </Text>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Активных пользователей"
              value={data?.unit_economics?.active_users ?? 0}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Платящих пользователей"
              value={data?.unit_economics?.paying_users ?? 0}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Cost per Active User"
              value={costPerUser}
              precision={4}
              prefix="$"
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card loading={isLoading}>
            <Statistic
              title="Cost per Paying User"
              value={costPerPayingUser}
              precision={4}
              prefix="$"
            />
          </Card>
        </Col>
      </Row>

        {/* Budget Alert (example - shows if cost exceeds threshold) */}
        {totalCost > 10 && (
          <Alert
            type="warning"
            message="Внимание: превышен бюджет"
            description={`Общая стоимость API ($${totalCost.toFixed(2)}) превысила $10 за выбранный период.`}
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}
      </div>
    </Spin>
  )
}
