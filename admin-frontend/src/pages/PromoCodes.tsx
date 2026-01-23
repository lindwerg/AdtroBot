import { useState } from 'react'
import { ProTable, ModalForm, ProFormText, ProFormDigit, ProFormDateTimePicker } from '@ant-design/pro-components'
import type { ProColumns } from '@ant-design/pro-components'
import { Button, Tag, Switch, message, Popconfirm, Progress } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  getPromoCodes,
  createPromoCode,
  updatePromoCode,
  deletePromoCode,
  type PromoCodeListItem,
} from '@/api/endpoints/promo'

export default function PromoCodesPage() {
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: createPromoCode,
    onSuccess: () => {
      message.success('Промокод создан')
      setCreateModalOpen(false)
      queryClient.invalidateQueries({ queryKey: ['promo-codes'] })
    },
    onError: () => message.error('Ошибка создания'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: { id: number } & Record<string, unknown>) =>
      updatePromoCode(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['promo-codes'] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deletePromoCode,
    onSuccess: () => {
      message.success('Удалено')
      queryClient.invalidateQueries({ queryKey: ['promo-codes'] })
    },
  })

  const columns: ProColumns<PromoCodeListItem>[] = [
    {
      dataIndex: 'code',
      title: 'Код',
      copyable: true,
      render: (_, r) => <Tag color="blue">{r.code}</Tag>,
    },
    {
      dataIndex: 'discount_percent',
      title: 'Скидка',
      render: (v) => `${v}%`,
      search: false,
    },
    {
      dataIndex: 'current_uses',
      title: 'Использований',
      render: (_, r) => {
        if (!r.max_uses) return r.current_uses
        return (
          <span>
            {r.current_uses}/{r.max_uses}
            <Progress
              percent={Math.round((r.current_uses / r.max_uses) * 100)}
              size="small"
              showInfo={false}
              style={{ width: 60, marginLeft: 8 }}
            />
          </span>
        )
      },
      search: false,
    },
    {
      dataIndex: 'valid_until',
      title: 'Действует до',
      render: (v) => v ? dayjs(v as string).format('DD.MM.YYYY') : 'Бессрочно',
      search: false,
    },
    {
      dataIndex: 'is_active',
      title: 'Активен',
      valueType: 'select',
      valueEnum: {
        true: { text: 'Да', status: 'Success' },
        false: { text: 'Нет', status: 'Default' },
      },
      render: (_, r) => (
        <Switch
          checked={r.is_active}
          onChange={(checked) =>
            updateMutation.mutate({ id: r.id, is_active: checked })
          }
        />
      ),
    },
    {
      dataIndex: 'created_at',
      title: 'Создан',
      render: (v) => dayjs(v as string).format('DD.MM.YYYY'),
      search: false,
    },
    {
      title: 'Действия',
      valueType: 'option',
      render: (_, r) => (
        <Popconfirm
          title="Удалить промокод?"
          onConfirm={() => deleteMutation.mutate(r.id)}
        >
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ]

  return (
    <>
      <ProTable<PromoCodeListItem>
        columns={columns}
        request={async (params) => {
          const { current, pageSize, ...filters } = params
          try {
            const data = await getPromoCodes({
              page: current,
              page_size: pageSize,
              is_active: filters.is_active === 'true' ? true :
                        filters.is_active === 'false' ? false : undefined,
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
        headerTitle="Промокоды"
        toolBarRender={() => [
          <Button
            key="create"
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalOpen(true)}
          >
            Создать
          </Button>,
        ]}
      />

      <ModalForm
        title="Создать промокод"
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onFinish={async (values) => {
          await createMutation.mutateAsync({
            code: values.code,
            discount_percent: values.discount_percent,
            valid_until: values.valid_until?.toISOString(),
            max_uses: values.max_uses,
          })
          return true
        }}
      >
        <ProFormText
          name="code"
          label="Код"
          placeholder="PROMO2024"
          rules={[{ required: true, message: 'Введите код' }]}
          fieldProps={{ style: { textTransform: 'uppercase' } }}
        />
        <ProFormDigit
          name="discount_percent"
          label="Скидка (%)"
          min={1}
          max={100}
          rules={[{ required: true, message: 'Укажите скидку' }]}
        />
        <ProFormDigit
          name="max_uses"
          label="Макс. использований"
          placeholder="Без ограничений"
          min={1}
        />
        <ProFormDateTimePicker
          name="valid_until"
          label="Действует до"
          placeholder="Бессрочно"
        />
      </ModalForm>
    </>
  )
}
