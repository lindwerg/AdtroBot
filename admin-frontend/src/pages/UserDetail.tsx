import { useParams, useNavigate } from 'react-router'
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Table,
  Typography,
  message,
  Modal,
  InputNumber,
  Spin,
  Alert,
} from 'antd'
import {
  ArrowLeftOutlined,
  CrownOutlined,
  StopOutlined,
  GiftOutlined,
  MessageOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { useUser, useUpdateSubscription, useGiftUser } from '@/hooks/useUsers'

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const userId = parseInt(id || '0')

  const { data: user, isLoading, error } = useUser(userId)
  const updateSubscription = useUpdateSubscription()
  const giftUser = useGiftUser()

  if (isLoading)
    return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (error || !user)
    return <Alert type="error" message="Пользователь не найден" showIcon />

  const handleActivate = () => {
    Modal.confirm({
      title: 'Активировать Premium?',
      content: 'Premium будет активирован на 30 дней',
      onOk: async () => {
        await updateSubscription.mutateAsync({ userId, request: { action: 'activate' } })
        message.success('Premium активирован')
      },
    })
  }

  const handleCancel = () => {
    Modal.confirm({
      title: 'Отменить Premium?',
      content: 'Premium доступ будет отключен немедленно',
      onOk: async () => {
        await updateSubscription.mutateAsync({ userId, request: { action: 'cancel' } })
        message.success('Premium отменен')
      },
    })
  }

  const handleExtend = () => {
    let days = 30
    Modal.confirm({
      title: 'Продлить Premium',
      content: (
        <InputNumber
          min={1}
          max={365}
          defaultValue={30}
          addonAfter="дней"
          onChange={(v) => {
            days = v || 30
          }}
          style={{ width: '100%', marginTop: 8 }}
        />
      ),
      onOk: async () => {
        await updateSubscription.mutateAsync({
          userId,
          request: { action: 'extend', days },
        })
        message.success(`Premium продлен на ${days} дней`)
      },
    })
  }

  const handleGift = (giftType: 'premium_days' | 'detailed_natal' | 'tarot_spreads') => {
    if (giftType === 'detailed_natal') {
      Modal.confirm({
        title: 'Подарить детальную натальную карту?',
        onOk: async () => {
          await giftUser.mutateAsync({
            userId,
            request: { gift_type: 'detailed_natal', value: 1 },
          })
          message.success('Подарок отправлен')
        },
      })
      return
    }

    let value = giftType === 'premium_days' ? 30 : 5
    Modal.confirm({
      title: giftType === 'premium_days' ? 'Подарить Premium дни' : 'Подарить расклады',
      content: (
        <InputNumber
          min={1}
          max={giftType === 'premium_days' ? 365 : 100}
          defaultValue={value}
          addonAfter={giftType === 'premium_days' ? 'дней' : 'раскладов'}
          onChange={(v) => {
            value = v || value
          }}
          style={{ width: '100%', marginTop: 8 }}
        />
      ),
      onOk: async () => {
        await giftUser.mutateAsync({ userId, request: { gift_type: giftType, value } })
        message.success('Подарок отправлен')
      },
    })
  }

  return (
    <div>
      <Button
        type="link"
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/users')}
        style={{ marginBottom: 16, paddingLeft: 0 }}
      >
        Назад к списку
      </Button>

      <Card
        title={
          <Space>
            <Typography.Text>Пользователь #{user.id}</Typography.Text>
            {user.is_premium && <Tag color="gold">Premium</Tag>}
          </Space>
        }
        extra={
          <Space>
            <Button icon={<MessageOutlined />}>Написать</Button>
            {user.is_premium ? (
              <>
                <Button icon={<CalendarOutlined />} onClick={handleExtend}>
                  Продлить
                </Button>
                <Button danger icon={<StopOutlined />} onClick={handleCancel}>
                  Отменить Premium
                </Button>
              </>
            ) : (
              <Button type="primary" icon={<CrownOutlined />} onClick={handleActivate}>
                Активировать Premium
              </Button>
            )}
          </Space>
        }
      >
        <Descriptions column={{ xs: 1, sm: 2, md: 3 }} bordered size="small">
          <Descriptions.Item label="Telegram ID">{user.telegram_id}</Descriptions.Item>
          <Descriptions.Item label="Username">{user.username || '-'}</Descriptions.Item>
          <Descriptions.Item label="Знак зодиака">{user.zodiac_sign || '-'}</Descriptions.Item>
          <Descriptions.Item label="Дата рождения">
            {user.birth_date ? dayjs(user.birth_date).format('DD.MM.YYYY') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Время рождения">{user.birth_time || '-'}</Descriptions.Item>
          <Descriptions.Item label="Город рождения">{user.birth_city || '-'}</Descriptions.Item>
          <Descriptions.Item label="Часовой пояс">{user.timezone || '-'}</Descriptions.Item>
          <Descriptions.Item label="Уведомления">
            {user.notifications_enabled ? `Да, в ${user.notification_hour}:00` : 'Нет'}
          </Descriptions.Item>
          <Descriptions.Item label="Регистрация">
            {dayjs(user.created_at).format('DD.MM.YYYY HH:mm')}
          </Descriptions.Item>
          <Descriptions.Item label="Premium до">
            {user.premium_until ? dayjs(user.premium_until).format('DD.MM.YYYY HH:mm') : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Лимит раскладов/день">
            {user.daily_spread_limit}
          </Descriptions.Item>
          <Descriptions.Item label="Раскладов сделано">{user.tarot_spread_count}</Descriptions.Item>
          <Descriptions.Item label="Детальная натальная">
            {user.detailed_natal_purchased_at ? (
              <Tag color="purple">
                Куплена {dayjs(user.detailed_natal_purchased_at).format('DD.MM.YYYY')}
              </Tag>
            ) : (
              '-'
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* Gifts section */}
      <Card title="Подарки" size="small" style={{ marginTop: 16 }}>
        <Space>
          <Button icon={<GiftOutlined />} onClick={() => handleGift('premium_days')}>
            Подарить Premium дни
          </Button>
          <Button icon={<GiftOutlined />} onClick={() => handleGift('tarot_spreads')}>
            Подарить расклады
          </Button>
          {!user.detailed_natal_purchased_at && (
            <Button icon={<GiftOutlined />} onClick={() => handleGift('detailed_natal')}>
              Подарить детальную натальную
            </Button>
          )}
        </Space>
      </Card>

      {/* Payment history */}
      <Card title="История платежей" size="small" style={{ marginTop: 16 }}>
        <Table
          dataSource={user.payments}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: 'ID', dataIndex: 'id', width: 100, ellipsis: true },
            {
              title: 'Сумма',
              dataIndex: 'amount',
              render: (v: number) => `${(v / 100).toFixed(0)} RUB`,
            },
            {
              title: 'Статус',
              dataIndex: 'status',
              render: (v: string) => (
                <Tag color={v === 'succeeded' ? 'green' : v === 'pending' ? 'orange' : 'red'}>
                  {v}
                </Tag>
              ),
            },
            { title: 'Описание', dataIndex: 'description', ellipsis: true },
            {
              title: 'Дата',
              dataIndex: 'paid_at',
              render: (v: string | null, r: { created_at: string }) =>
                dayjs(v || r.created_at).format('DD.MM.YYYY HH:mm'),
            },
          ]}
        />
      </Card>

      {/* Spread history */}
      <Card title="Последние расклады" size="small" style={{ marginTop: 16 }}>
        <Table
          dataSource={user.recent_spreads}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            {
              title: 'Тип',
              dataIndex: 'spread_type',
              render: (v: string) => (v === 'celtic_cross' ? 'Кельтский крест' : '3 карты'),
            },
            { title: 'Вопрос', dataIndex: 'question', ellipsis: true },
            {
              title: 'Дата',
              dataIndex: 'created_at',
              render: (v: string) => dayjs(v).format('DD.MM.YYYY HH:mm'),
            },
          ]}
        />
      </Card>
    </div>
  )
}
