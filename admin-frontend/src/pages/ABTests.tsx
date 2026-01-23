import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Tag,
  Row,
  Col,
  Statistic,
  Typography,
  Modal,
  Form,
  Input,
  Select,
  Slider,
  message,
  Space,
} from 'antd'
import {
  PlusOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  TrophyOutlined,
  BarChartOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getExperiments,
  createExperiment,
  startExperiment,
  stopExperiment,
  getExperimentResults,
  getUTMAnalytics,
} from '@/api/endpoints/experiments'
import type { ExperimentListItem } from '@/api/endpoints/experiments'

export default function ABTestsPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [resultsModal, setResultsModal] = useState<{
    open: boolean
    id: number | null
  }>({ open: false, id: null })
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data: experiments } = useQuery({
    queryKey: ['experiments'],
    queryFn: () => getExperiments(),
  })

  const { data: results } = useQuery({
    queryKey: ['experiment-results', resultsModal.id],
    queryFn: () => getExperimentResults(resultsModal.id!),
    enabled: resultsModal.id !== null,
  })

  const { data: utmData } = useQuery({
    queryKey: ['utm-analytics'],
    queryFn: getUTMAnalytics,
  })

  const createMutation = useMutation({
    mutationFn: createExperiment,
    onSuccess: () => {
      message.success('Эксперимент создан')
      setCreateModalOpen(false)
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
  })

  const startMutation = useMutation({
    mutationFn: startExperiment,
    onSuccess: () => {
      message.success('Эксперимент запущен')
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
  })

  const stopMutation = useMutation({
    mutationFn: stopExperiment,
    onSuccess: () => {
      message.success('Эксперимент остановлен')
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
  })

  const columns = [
    { dataIndex: 'name', title: 'Название' },
    {
      dataIndex: 'metric',
      title: 'Метрика',
      render: (v: string) => {
        const labels: Record<string, string> = {
          conversion: 'Конверсия',
          retention: 'Retention',
          revenue: 'Доход',
        }
        return labels[v] || v
      },
    },
    {
      dataIndex: 'variant_b_percent',
      title: 'Распределение',
      render: (v: number) => `A: ${100 - v}% / B: ${v}%`,
    },
    {
      dataIndex: 'status',
      title: 'Статус',
      render: (v: string) => {
        const colors: Record<string, string> = {
          draft: 'default',
          running: 'processing',
          paused: 'warning',
          completed: 'success',
        }
        const labels: Record<string, string> = {
          draft: 'Черновик',
          running: 'Запущен',
          paused: 'Пауза',
          completed: 'Завершен',
        }
        return <Tag color={colors[v]}>{labels[v] || v}</Tag>
      },
    },
    {
      title: 'Действия',
      render: (_: unknown, r: ExperimentListItem) => (
        <Space>
          {r.status === 'draft' && (
            <Button
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => startMutation.mutate(r.id)}
              loading={startMutation.isPending}
            >
              Запустить
            </Button>
          )}
          {r.status === 'running' && (
            <Button
              size="small"
              icon={<PauseCircleOutlined />}
              onClick={() => stopMutation.mutate(r.id)}
              loading={stopMutation.isPending}
            >
              Остановить
            </Button>
          )}
          <Button
            size="small"
            icon={<BarChartOutlined />}
            onClick={() => setResultsModal({ open: true, id: r.id })}
          >
            Результаты
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={14}>
        <Card
          title="A/B тесты"
          extra={
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalOpen(true)}
            >
              Создать
            </Button>
          }
        >
          <Table
            dataSource={experiments?.items}
            columns={columns}
            rowKey="id"
            pagination={{ total: experiments?.total, pageSize: 20 }}
          />
        </Card>
      </Col>

      <Col xs={24} lg={10}>
        <Card title="UTM источники">
          {utmData?.sources && utmData.sources.length > 0 ? (
            <Table
              dataSource={utmData?.sources}
              rowKey="source"
              pagination={false}
              size="small"
              columns={[
                { dataIndex: 'source', title: 'Источник' },
                { dataIndex: 'users', title: 'Юзеры' },
                {
                  dataIndex: 'conversion_rate',
                  title: 'Конверсия',
                  render: (v: number) => `${v}%`,
                },
                {
                  dataIndex: 'total_revenue',
                  title: 'Доход',
                  render: (v: number) => `${(v / 100).toFixed(0)} RUB`,
                },
              ]}
            />
          ) : (
            <Typography.Text type="secondary">
              Нет данных по UTM источникам. Добавьте ?utm_source=... к ссылкам на бота.
            </Typography.Text>
          )}
        </Card>
      </Col>

      {/* Create Modal */}
      <Modal
        title="Создать эксперимент"
        open={createModalOpen}
        onCancel={() => setCreateModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => createMutation.mutate(values)}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input placeholder="Тест новой онбординг-страницы" />
          </Form.Item>
          <Form.Item name="description" label="Описание">
            <Input.TextArea
              placeholder="Описание эксперимента и гипотезы"
              rows={3}
            />
          </Form.Item>
          <Form.Item
            name="metric"
            label="Метрика"
            rules={[{ required: true, message: 'Выберите метрику' }]}
          >
            <Select
              placeholder="Выберите метрику"
              options={[
                { value: 'conversion', label: 'Конверсия в оплату' },
                { value: 'retention', label: 'Retention D7' },
                { value: 'revenue', label: 'Средний чек' },
              ]}
            />
          </Form.Item>
          <Form.Item
            name="variant_b_percent"
            label="% пользователей в варианте B"
            initialValue={50}
          >
            <Slider
              min={10}
              max={90}
              marks={{ 10: '10%', 50: '50%', 90: '90%' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Results Modal */}
      <Modal
        title="Результаты эксперимента"
        open={resultsModal.open}
        onCancel={() => setResultsModal({ open: false, id: null })}
        footer={null}
        width={600}
      >
        {results && (
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card
                size="small"
                title={
                  <span>
                    Вариант A {results.winner === 'A' && <TrophyOutlined style={{ color: '#faad14' }} />}
                  </span>
                }
              >
                <Statistic title="Пользователей" value={results.variant_a.users} />
                <Statistic
                  title="Конверсий"
                  value={results.variant_a.conversions}
                />
                <Statistic
                  title="Конверсия"
                  value={results.variant_a.conversion_rate}
                  suffix="%"
                  valueStyle={{
                    color: results.winner === 'A' ? '#3f8600' : undefined,
                  }}
                />
              </Card>
            </Col>
            <Col span={12}>
              <Card
                size="small"
                title={
                  <span>
                    Вариант B {results.winner === 'B' && <TrophyOutlined style={{ color: '#faad14' }} />}
                  </span>
                }
              >
                <Statistic title="Пользователей" value={results.variant_b.users} />
                <Statistic
                  title="Конверсий"
                  value={results.variant_b.conversions}
                />
                <Statistic
                  title="Конверсия"
                  value={results.variant_b.conversion_rate}
                  suffix="%"
                  valueStyle={{
                    color: results.winner === 'B' ? '#3f8600' : undefined,
                  }}
                />
              </Card>
            </Col>
            {results.winner && (
              <Col span={24}>
                <Typography.Text type="success">
                  <TrophyOutlined /> Победитель: Вариант {results.winner} (разница{' '}
                  {Math.abs(
                    results.variant_a.conversion_rate -
                      results.variant_b.conversion_rate
                  ).toFixed(2)}
                  %)
                </Typography.Text>
              </Col>
            )}
            {!results.winner &&
              (results.variant_a.users < 100 ||
                results.variant_b.users < 100) && (
                <Col span={24}>
                  <Typography.Text type="secondary">
                    Недостаточно данных для определения победителя (нужно минимум 100
                    пользователей в каждом варианте)
                  </Typography.Text>
                </Col>
              )}
          </Row>
        )}
      </Modal>
    </Row>
  )
}
