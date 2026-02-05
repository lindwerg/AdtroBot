import { useState } from 'react'
import {
  ProTable,
  ModalForm,
  ProFormText,
  ProFormDigit,
  ProFormDateTimePicker,
  ProFormSelect,
} from '@ant-design/pro-components'
import type { ProColumns } from '@ant-design/pro-components'
import { Button, Tag, Switch, message, Popconfirm } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  getGlobalDiscounts,
  createGlobalDiscount,
  updateGlobalDiscount,
  deleteGlobalDiscount,
  type GlobalDiscountListItem,
} from '@/api/endpoints/discounts'

const planLabels: Record<string, string> = {
  monthly: 'Месяц',
  yearly: 'Год',
  all: 'Все планы',
}

export default function GlobalDiscountsPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: createGlobalDiscount,
    onSuccess: () => {
      message.success('Акция создана')
      setCreateModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['global-discounts'] })
    },
    onError: () => message.error('Ошибка создания'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Record<string, unknown>) =>
      updateGlobalDiscount(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['global-discounts'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteGlobalDiscount,
    onSuccess: () => {
      message.success('Удалено')
      queryClient.invalidateQueries({ queryKey: ['global-discounts'] })
    },
  })

  const columns: ProColumns<GlobalDiscountListItem>[] = [
    {
      dataIndex: 'name',
      title: 'Название',
      width: 200,
    },
    {
      dataIndex: 'target_plan',
      title: 'План',
      render: (_, r) => <Tag color="blue">{planLabels[r.target_plan] || r.target_plan}</Tag>,
      valueType: 'select',
      valueEnum: {
        monthly: { text: 'Месяц' },
        yearly: { text: 'Год' },
        all: { text: 'Все' },
      },
    },
    {
      dataIndex: 'discount_percent',
      title: 'Скидка',
      render: (v) => <Tag color="red">{v}%</Tag>,
      search: false,
    },
    {
      dataIndex: 'active_until',
      title: 'Действует до',
      render: (v) => (v ? dayjs(v as string).format('DD.MM.YYYY HH:mm') : 'Бессрочно'),
      search: false,
    },
    {
      dataIndex: 'is_active',
      title: 'Активна',
      valueType: 'select',
      valueEnum: {
        true: { text: 'Да', status: 'Success' },
        false: { text: 'Нет', status: 'Default' },
      },
      render: (_, r) => (
        <Switch
          checked={r.is_active}
          onChange={(checked) => updateMutation.mutate({ id: r.id, is_active: checked })}
        />
      ),
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
      render: (_, r) => (
        <Popconfirm title="Удалить акцию?" onConfirm={() => deleteMutation.mutate(r.id)}>
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <ProTable<GlobalDiscountListItem>
        columns={columns}
        request={async (params) => {
          const { current, pageSize, ...filters } = params
          try {
            const data = await getGlobalDiscounts({
              page: current,
              page_size: pageSize,
              is_active:
                filters.is_active === 'true'
                  ? true
                  : filters.is_active === 'false'
                    ? false
                    : undefined,
              target_plan: filters.target_plan,
            })
            return { data: data.items, total: data.total, success: true }
          } catch {
            return { data: [], total: 0, success: false }
          }
        }}
        rowKey="id"
        pagination={{ pageSize: 20 }}
        search={{ filterType: 'light' }}
        headerTitle="Глобальные скидки"
        toolBarRender={() => [
          <Button
            key="create"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalOpen(true)}
          >
            Создать акцию
          </Button>,
        ]}
      />

      <ModalForm
        title="Создать глобальную скидку"
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={async (values) => {
          await createMutation.mutateAsync({
            name: values.name,
            target_plan: values.target_plan,
            discount_percent: values.discount_percent,
            active_until: values.active_until
              ? dayjs(values.active_until).toISOString()
              : undefined,
          })
          return true
        }}
      >
        <ProFormText
          name="name"
          label="Название акции"
          placeholder="Скидка 50% на месяц"
          rules={[{ required: true, message: 'Введите название' }]}
        />
        <ProFormSelect
          name="target_plan"
          label="План подписки"
          options={[
            { label: 'Месячный', value: 'monthly' },
            { label: 'Годовой', value: 'yearly' },
            { label: 'Все планы', value: 'all' },
          ]}
          rules={[{ required: true, message: 'Выберите план' }]}
        />
        <ProFormDigit
          name="discount_percent"
          label="Скидка (%)"
          min={1}
          max={99}
          rules={[{ required: true, message: 'Укажите скидку' }]}
          fieldProps={{ precision: 0 }}
        />
        <ProFormDateTimePicker name="active_until" label="Действует до" placeholder="Бессрочно" />
      </ModalForm>
    </>
  )
}
