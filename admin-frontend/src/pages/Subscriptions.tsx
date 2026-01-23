import { ProTable } from '@ant-design/pro-components'
import type { ProColumns } from '@ant-design/pro-components'
import { Tag, Button, Modal, Select, message } from 'antd'
import { EditOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { Link } from 'react-router'
import { getSubscriptions, updateSubscriptionStatus } from '@/api/endpoints/payments'
import type { SubscriptionListItem } from '@/api/endpoints/payments'

export default function SubscriptionsPage() {
  const [editModal, setEditModal] = useState<{
    open: boolean
    sub: SubscriptionListItem | null
  }>({
    open: false,
    sub: null,
  })
  const [newStatus, setNewStatus] = useState('')
  const [tableKey, setTableKey] = useState(0)

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateSubscriptionStatus(id, status),
    onSuccess: () => {
      message.success('Статус обновлен')
      setEditModal({ open: false, sub: null })
      setTableKey((k) => k + 1)
    },
    onError: () => {
      message.error('Ошибка обновления статуса')
    },
  })

  const columns: ProColumns<SubscriptionListItem>[] = [
    { dataIndex: 'id', title: 'ID', width: 60, search: false },
    {
      dataIndex: 'user_telegram_id',
      title: 'Пользователь',
      render: (_, r) => {
        const label = r.user_username || r.user_telegram_id || '\u2014'
        return <Link to={`/users/${r.user_id}`}>{label}</Link>
      },
    },
    {
      dataIndex: 'plan',
      title: 'План',
      valueType: 'select',
      valueEnum: {
        monthly: { text: 'Месяц' },
        yearly: { text: 'Год' },
      },
    },
    {
      dataIndex: 'status',
      title: 'Статус',
      valueType: 'select',
      valueEnum: {
        trial: { text: 'Триал', status: 'Processing' },
        active: { text: 'Активна', status: 'Success' },
        past_due: { text: 'Просрочена', status: 'Warning' },
        canceled: { text: 'Отменена', status: 'Default' },
        expired: { text: 'Истекла', status: 'Error' },
      },
      render: (_, r) => {
        const colors: Record<string, string> = {
          trial: 'blue',
          active: 'green',
          past_due: 'orange',
          canceled: 'default',
          expired: 'red',
        }
        return <Tag color={colors[r.status] || 'default'}>{r.status}</Tag>
      },
    },
    {
      dataIndex: 'current_period_end',
      title: 'Действует до',
      render: (v) => dayjs(v as string).format('DD.MM.YYYY'),
      search: false,
    },
    {
      dataIndex: 'canceled_at',
      title: 'Отменена',
      render: (v) => (v ? dayjs(v as string).format('DD.MM.YYYY') : '\u2014'),
      search: false,
    },
    {
      dataIndex: 'created_at',
      title: 'Создана',
      render: (v) => dayjs(v as string).format('DD.MM.YYYY'),
      search: false,
    },
    {
      title: 'Действия',
      valueType: 'option',
      width: 120,
      render: (_, r) => (
        <Button
          size="small"
          icon={<EditOutlined />}
          onClick={() => {
            setEditModal({ open: true, sub: r })
            setNewStatus(r.status)
          }}
        >
          Изменить
        </Button>
      ),
    },
  ]

  return (
    <>
      <ProTable<SubscriptionListItem>
        key={tableKey}
        columns={columns}
        request={async (params) => {
          const { current, pageSize, ...filters } = params
          try {
            const data = await getSubscriptions({
              page: current,
              page_size: pageSize,
              status: filters.status,
              plan: filters.plan,
              user_search: filters.user_telegram_id,
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
        pagination={{ pageSize: 20 }}
        search={{ filterType: 'light' }}
        headerTitle="Подписки"
      />

      <Modal
        title="Изменить статус подписки"
        open={editModal.open}
        onCancel={() => setEditModal({ open: false, sub: null })}
        onOk={() => {
          if (editModal.sub) {
            updateMutation.mutate({ id: editModal.sub.id, status: newStatus })
          }
        }}
        confirmLoading={updateMutation.isPending}
      >
        <Select
          value={newStatus}
          onChange={setNewStatus}
          style={{ width: '100%' }}
          options={[
            { value: 'trial', label: 'Триал' },
            { value: 'active', label: 'Активна' },
            { value: 'past_due', label: 'Просрочена' },
            { value: 'canceled', label: 'Отменена' },
            { value: 'expired', label: 'Истекла' },
          ]}
        />
      </Modal>
    </>
  )
}
