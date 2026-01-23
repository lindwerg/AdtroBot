import { ProTable } from '@ant-design/pro-components'
import type { ProColumns } from '@ant-design/pro-components'
import { Tag, Statistic, Card, Row, Col, Button } from 'antd'
import { ExportOutlined } from '@ant-design/icons'
import { useState } from 'react'
import dayjs from 'dayjs'
import { getPayments } from '@/api/endpoints/payments'
import type { PaymentListItem } from '@/api/endpoints/payments'

const columns: ProColumns<PaymentListItem>[] = [
  {
    dataIndex: 'id',
    title: 'ID',
    copyable: true,
    width: 100,
    ellipsis: true,
    search: false,
  },
  {
    dataIndex: 'user_telegram_id',
    title: 'Пользователь',
    render: (_, r) => r.user_username || r.user_telegram_id || '\u2014',
  },
  {
    dataIndex: 'amount',
    title: 'Сумма',
    render: (v) => `${((v as number) / 100).toFixed(0)} RUB`,
    search: false,
  },
  {
    dataIndex: 'status',
    title: 'Статус',
    valueType: 'select',
    valueEnum: {
      pending: { text: 'Ожидает', status: 'Processing' },
      waiting_for_capture: { text: 'Capture', status: 'Warning' },
      succeeded: { text: 'Успешно', status: 'Success' },
      canceled: { text: 'Отменен', status: 'Error' },
    },
    render: (_, r) => {
      const colors: Record<string, string> = {
        pending: 'orange',
        waiting_for_capture: 'blue',
        succeeded: 'green',
        canceled: 'red',
      }
      return <Tag color={colors[r.status] || 'default'}>{r.status}</Tag>
    },
  },
  {
    dataIndex: 'is_recurring',
    title: 'Автоплатеж',
    render: (v) => (v ? 'Да' : 'Нет'),
    search: false,
    width: 100,
  },
  {
    dataIndex: 'description',
    title: 'Описание',
    ellipsis: true,
    search: false,
  },
  {
    dataIndex: 'paid_at',
    title: 'Оплачен',
    render: (_, r) => (r.paid_at ? dayjs(r.paid_at).format('DD.MM.YYYY HH:mm') : '\u2014'),
    search: false,
  },
  {
    dataIndex: 'created_at',
    title: 'Создан',
    render: (_, r) => dayjs(r.created_at).format('DD.MM.YYYY HH:mm'),
    search: false,
  },
]

export default function PaymentsPage() {
  const [totalAmount, setTotalAmount] = useState(0)

  return (
    <>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Успешные платежи (фильтр)"
              value={totalAmount / 100}
              suffix="RUB"
              precision={0}
            />
          </Card>
        </Col>
      </Row>

      <ProTable<PaymentListItem>
        columns={columns}
        request={async (params) => {
          const { current, pageSize, ...filters } = params
          try {
            const data = await getPayments({
              page: current,
              page_size: pageSize,
              status: filters.status,
              user_search: filters.user_telegram_id,
            })
            setTotalAmount(data.total_amount)
            return {
              data: data.items,
              total: data.total,
              success: true,
            }
          } catch {
            return { data: [], total: 0, success: false }
          }
        }}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        search={{ filterType: 'light' }}
        headerTitle="Платежи"
        toolBarRender={() => [
          <Button
            key="export"
            icon={<ExportOutlined />}
            onClick={() => window.open('/admin/export/payments', '_blank')}
          >
            Экспорт CSV
          </Button>,
        ]}
      />
    </>
  )
}
