import { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Select,
  DatePicker,
  Table,
  Tag,
  Space,
  message,
  Row,
  Col,
  Switch,
} from 'antd'
import { SendOutlined, ClockCircleOutlined, DeleteOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  sendMessage,
  getMessageHistory,
  cancelMessage,
  type MessageHistoryItem,
  type SendMessageRequest,
} from '@/api/endpoints/messages'

const ZODIAC_OPTIONS = [
  { value: 'aries', label: 'Овен' },
  { value: 'taurus', label: 'Телец' },
  { value: 'gemini', label: 'Близнецы' },
  { value: 'cancer', label: 'Рак' },
  { value: 'leo', label: 'Лев' },
  { value: 'virgo', label: 'Дева' },
  { value: 'libra', label: 'Весы' },
  { value: 'scorpio', label: 'Скорпион' },
  { value: 'sagittarius', label: 'Стрелец' },
  { value: 'capricorn', label: 'Козерог' },
  { value: 'aquarius', label: 'Водолей' },
  { value: 'pisces', label: 'Рыбы' },
]

interface FormValues {
  text: string
  target_user_id?: number
  is_premium?: boolean
  zodiac_sign?: string
  scheduled_at?: dayjs.Dayjs
}

export default function MessagesPage() {
  const [form] = Form.useForm<FormValues>()
  const [isBroadcast, setIsBroadcast] = useState(true)
  const [isScheduled, setIsScheduled] = useState(false)
  const queryClient = useQueryClient()

  const { data: history, isLoading } = useQuery({
    queryKey: ['messages'],
    queryFn: () => getMessageHistory(),
  })

  const sendMutation = useMutation({
    mutationFn: sendMessage,
    onSuccess: (result) => {
      message.success(
        result.status === 'scheduled'
          ? 'Сообщение запланировано'
          : `Доставлено: ${result.recipients_count}`
      )
      form.resetFields()
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
    onError: () => message.error('Ошибка отправки'),
  })

  const cancelMutation = useMutation({
    mutationFn: cancelMessage,
    onSuccess: () => {
      message.success('Отменено')
      queryClient.invalidateQueries({ queryKey: ['messages'] })
    },
  })

  const onFinish = (values: FormValues) => {
    const request: SendMessageRequest = { text: values.text }

    if (!isBroadcast && values.target_user_id) {
      request.target_user_id = values.target_user_id
    } else {
      const filters: Record<string, unknown> = {}
      if (values.is_premium !== undefined) filters.is_premium = values.is_premium
      if (values.zodiac_sign) filters.zodiac_sign = values.zodiac_sign
      request.filters = filters
    }

    if (isScheduled && values.scheduled_at) {
      request.scheduled_at = values.scheduled_at.toISOString()
    }

    sendMutation.mutate(request)
  }

  const columns = [
    {
      title: 'Текст',
      dataIndex: 'text',
      ellipsis: true,
      width: 200,
    },
    {
      title: 'Получатели',
      key: 'recipients',
      render: (_: unknown, r: MessageHistoryItem) => (
        <span>
          {r.target_user_id ? `User #${r.target_user_id}` : 'Рассылка'}{' '}
          <Tag>
            {r.delivered_count}/{r.total_recipients}
          </Tag>
        </span>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      render: (v: string) => {
        const colors: Record<string, string> = {
          sent: 'green',
          pending: 'orange',
          sending: 'blue',
          canceled: 'red',
        }
        return <Tag color={colors[v]}>{v}</Tag>
      },
    },
    {
      title: 'Дата',
      key: 'date',
      render: (_: unknown, r: MessageHistoryItem) =>
        dayjs(r.sent_at || r.scheduled_at || r.created_at).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: unknown, r: MessageHistoryItem) =>
        r.status === 'pending' && (
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => cancelMutation.mutate(r.id)}
          />
        ),
    },
  ]

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={10}>
        <Card title="Отправить сообщение">
          <Form form={form} layout="vertical" onFinish={onFinish}>
            <Form.Item
              name="text"
              label="Текст сообщения"
              rules={[{ required: true, message: 'Введите текст' }]}
            >
              <Input.TextArea rows={4} placeholder="Текст сообщения..." />
            </Form.Item>

            <Space style={{ marginBottom: 16 }}>
              <Switch
                checked={isBroadcast}
                onChange={setIsBroadcast}
                checkedChildren="Рассылка"
                unCheckedChildren="Одному"
              />
              <Switch
                checked={isScheduled}
                onChange={setIsScheduled}
                checkedChildren="Отложить"
                unCheckedChildren="Сейчас"
              />
            </Space>

            {!isBroadcast ? (
              <Form.Item
                name="target_user_id"
                label="ID пользователя"
                rules={[{ required: true, message: 'Укажите ID' }]}
              >
                <Input type="number" placeholder="User ID" />
              </Form.Item>
            ) : (
              <>
                <Form.Item name="is_premium" label="Статус">
                  <Select allowClear placeholder="Все">
                    <Select.Option value={true}>Premium</Select.Option>
                    <Select.Option value={false}>Free</Select.Option>
                  </Select>
                </Form.Item>
                <Form.Item name="zodiac_sign" label="Знак зодиака">
                  <Select allowClear placeholder="Все" options={ZODIAC_OPTIONS} />
                </Form.Item>
              </>
            )}

            {isScheduled && (
              <Form.Item
                name="scheduled_at"
                label="Дата и время"
                rules={[{ required: true, message: 'Выберите время' }]}
              >
                <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            )}

            <Button
              type="primary"
              htmlType="submit"
              icon={isScheduled ? <ClockCircleOutlined /> : <SendOutlined />}
              loading={sendMutation.isPending}
              block
            >
              {isScheduled ? 'Запланировать' : 'Отправить'}
            </Button>
          </Form>
        </Card>
      </Col>

      <Col xs={24} lg={14}>
        <Card title="История сообщений">
          <Table
            dataSource={history?.items}
            columns={columns}
            rowKey="id"
            loading={isLoading}
            pagination={{
              total: history?.total,
              pageSize: 20,
            }}
            size="small"
          />
        </Card>
      </Col>
    </Row>
  )
}
