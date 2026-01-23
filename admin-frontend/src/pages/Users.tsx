import { useState } from 'react'
import { useNavigate } from 'react-router'
import { ProTable, ProColumns } from '@ant-design/pro-components'
import { Button, Tag, Space, message, Modal, InputNumber } from 'antd'
import { UserOutlined, GiftOutlined, ExportOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { getUsers, UserListItem, bulkAction } from '@/api/endpoints/users'

const ZODIAC_SIGNS = [
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

const columns: ProColumns<UserListItem>[] = [
  {
    dataIndex: 'telegram_id',
    title: 'Telegram ID',
    copyable: true,
    width: 120,
  },
  {
    dataIndex: 'username',
    title: 'Username',
    render: (_, record) => record.username || '-',
  },
  {
    dataIndex: 'zodiac_sign',
    title: 'Знак',
    valueType: 'select',
    valueEnum: Object.fromEntries(ZODIAC_SIGNS.map((z) => [z.value, { text: z.label }])),
    width: 100,
  },
  {
    dataIndex: 'is_premium',
    title: 'Статус',
    valueType: 'select',
    valueEnum: {
      true: { text: 'Premium', status: 'Success' },
      false: { text: 'Free', status: 'Default' },
    },
    render: (_, record) => (
      <Tag color={record.is_premium ? 'gold' : 'default'}>
        {record.is_premium ? 'Premium' : 'Free'}
      </Tag>
    ),
    width: 100,
  },
  {
    dataIndex: 'premium_until',
    title: 'Premium до',
    valueType: 'dateTime',
    render: (_, record) =>
      record.premium_until ? dayjs(record.premium_until).format('DD.MM.YYYY') : '-',
    search: false,
    width: 110,
  },
  {
    dataIndex: 'tarot_spread_count',
    title: 'Раскладов',
    search: false,
    width: 90,
  },
  {
    dataIndex: 'detailed_natal_purchased_at',
    title: 'Детальная натальная',
    render: (_, record) =>
      record.detailed_natal_purchased_at ? <Tag color="purple">Куплена</Tag> : '-',
    valueType: 'select',
    valueEnum: {
      true: { text: 'Куплена' },
      false: { text: 'Нет' },
    },
    width: 130,
  },
  {
    dataIndex: 'created_at',
    title: 'Регистрация',
    valueType: 'dateTime',
    render: (_, record) => dayjs(record.created_at).format('DD.MM.YYYY'),
    search: false,
    sorter: true,
    width: 110,
  },
  {
    title: 'Действия',
    valueType: 'option',
    width: 80,
    render: (_, record) => [
      <Button
        key="view"
        type="link"
        size="small"
        icon={<UserOutlined />}
        onClick={() => (window.location.href = `/users/${record.id}`)}
      >
        Открыть
      </Button>,
    ],
  },
]

export default function UsersPage() {
  const navigate = useNavigate()
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [actionKey, setActionKey] = useState(0)

  const handleBulkAction = async (action: string, value?: number) => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите пользователей')
      return
    }

    try {
      const result = await bulkAction({
        user_ids: selectedRowKeys,
        action: action as 'activate_premium' | 'cancel_premium' | 'ban' | 'unban' | 'gift_spreads',
        value,
      })
      message.success(`Успешно: ${result.success_count}, ошибок: ${result.failed_count}`)
      setSelectedRowKeys([])
      setActionKey((k) => k + 1)
    } catch {
      message.error('Ошибка выполнения')
    }
  }

  return (
    <ProTable<UserListItem>
      key={actionKey}
      columns={columns}
      request={async (params, sort) => {
        const { current, pageSize, keyword, ...filters } = params
        const sortField = Object.keys(sort || {})[0]
        const sortOrder = sortField
          ? sort[sortField] === 'descend'
            ? 'desc'
            : 'asc'
          : undefined

        try {
          const data = await getUsers({
            page: current,
            page_size: pageSize,
            search: keyword,
            zodiac_sign: filters.zodiac_sign,
            is_premium:
              filters.is_premium === 'true'
                ? true
                : filters.is_premium === 'false'
                  ? false
                  : undefined,
            has_detailed_natal:
              filters.detailed_natal_purchased_at === 'true'
                ? true
                : filters.detailed_natal_purchased_at === 'false'
                  ? false
                  : undefined,
            sort_by: sortField,
            sort_order: sortOrder,
          })
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
      pagination={{ pageSize: 20, showSizeChanger: true }}
      search={{ filterType: 'light' }}
      options={{
        search: { placeholder: 'Telegram ID или username' },
      }}
      rowSelection={{
        selectedRowKeys,
        onChange: (keys) => setSelectedRowKeys(keys as number[]),
      }}
      tableAlertOptionRender={() => (
        <Space>
          <Button size="small" onClick={() => handleBulkAction('activate_premium')}>
            Активировать Premium
          </Button>
          <Button size="small" onClick={() => handleBulkAction('cancel_premium')}>
            Отменить Premium
          </Button>
          <Button
            size="small"
            icon={<GiftOutlined />}
            onClick={() => {
              let giftCount = 5
              Modal.confirm({
                title: 'Подарить расклады',
                content: (
                  <InputNumber
                    min={1}
                    max={100}
                    defaultValue={5}
                    style={{ width: '100%', marginTop: 8 }}
                    onChange={(v) => {
                      giftCount = v || 5
                    }}
                  />
                ),
                onOk: () => handleBulkAction('gift_spreads', giftCount),
              })
            }}
          >
            Подарить расклады
          </Button>
        </Space>
      )}
      onRow={(record) => ({
        onClick: () => navigate(`/users/${record.id}`),
        style: { cursor: 'pointer' },
      })}
      headerTitle="Пользователи"
      toolBarRender={() => [
        <Button key="export" icon={<ExportOutlined />}>
          Экспорт CSV
        </Button>,
      ]}
    />
  )
}
