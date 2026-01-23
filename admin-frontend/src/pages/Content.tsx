import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  message,
  Tag,
  Typography,
} from 'antd'
import { EditOutlined, SaveOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  getHoroscopeContent,
  updateHoroscopeContent,
  HoroscopeContentItem,
} from '@/api/endpoints/content'

const ZODIAC_LABELS: Record<string, string> = {
  aries: 'Овен',
  taurus: 'Телец',
  gemini: 'Близнецы',
  cancer: 'Рак',
  leo: 'Лев',
  virgo: 'Дева',
  libra: 'Весы',
  scorpio: 'Скорпион',
  sagittarius: 'Стрелец',
  capricorn: 'Козерог',
  aquarius: 'Водолей',
  pisces: 'Рыбы',
}

const ZODIAC_EMOJI: Record<string, string> = {
  aries: '\u2648',
  taurus: '\u2649',
  gemini: '\u264A',
  cancer: '\u264B',
  leo: '\u264C',
  virgo: '\u264D',
  libra: '\u264E',
  scorpio: '\u264F',
  sagittarius: '\u2650',
  capricorn: '\u2651',
  aquarius: '\u2652',
  pisces: '\u2653',
}

export default function ContentPage() {
  const [editModal, setEditModal] = useState<{
    open: boolean
    item: HoroscopeContentItem | null
  }>({
    open: false,
    item: null,
  })
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['horoscope-content'],
    queryFn: getHoroscopeContent,
  })

  const updateMutation = useMutation({
    mutationFn: ({
      zodiacSign,
      request,
    }: {
      zodiacSign: string
      request: { base_text: string; notes?: string }
    }) => updateHoroscopeContent(zodiacSign, request),
    onSuccess: () => {
      message.success('Контент сохранен')
      setEditModal({ open: false, item: null })
      queryClient.invalidateQueries({ queryKey: ['horoscope-content'] })
    },
    onError: () => message.error('Ошибка сохранения'),
  })

  const openEditModal = (item: HoroscopeContentItem) => {
    setEditModal({ open: true, item })
    form.setFieldsValue({
      base_text: item.base_text,
      notes: item.notes,
    })
  }

  const handleSave = () => {
    form.validateFields().then((values) => {
      if (editModal.item) {
        updateMutation.mutate({
          zodiacSign: editModal.item.zodiac_sign,
          request: values,
        })
      }
    })
  }

  const columns = [
    {
      title: 'Знак',
      key: 'zodiac',
      width: 150,
      render: (_: unknown, r: HoroscopeContentItem) => (
        <span>
          {ZODIAC_EMOJI[r.zodiac_sign]} {ZODIAC_LABELS[r.zodiac_sign] || r.zodiac_sign}
        </span>
      ),
    },
    {
      title: 'Текст',
      dataIndex: 'base_text',
      ellipsis: true,
      render: (v: string) =>
        v ? (
          <Typography.Text ellipsis style={{ maxWidth: 400 }}>
            {v}
          </Typography.Text>
        ) : (
          <Tag color="default">Пусто</Tag>
        ),
    },
    {
      title: 'Обновлено',
      dataIndex: 'updated_at',
      width: 150,
      render: (v: string) => dayjs(v).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      render: (_: unknown, r: HoroscopeContentItem) => (
        <Button
          type="primary"
          size="small"
          icon={<EditOutlined />}
          onClick={() => openEditModal(r)}
        >
          Редактировать
        </Button>
      ),
    },
  ]

  return (
    <>
      <Card title="Контент гороскопов">
        <Typography.Paragraph type="secondary" style={{ marginBottom: 16 }}>
          Редактируйте базовые тексты гороскопов для каждого знака зодиака. Эти тексты
          используются как дополнительный контекст для AI генерации.
        </Typography.Paragraph>

        <Table
          dataSource={data?.items}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={false}
        />
      </Card>

      <Modal
        title={
          editModal.item
            ? `Редактировать: ${ZODIAC_EMOJI[editModal.item.zodiac_sign]} ${ZODIAC_LABELS[editModal.item.zodiac_sign]}`
            : 'Редактировать'
        }
        open={editModal.open}
        onCancel={() => setEditModal({ open: false, item: null })}
        onOk={handleSave}
        okText="Сохранить"
        okButtonProps={{ icon: <SaveOutlined />, loading: updateMutation.isPending }}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="base_text"
            label="Базовый текст гороскопа"
            rules={[{ max: 5000, message: 'Максимум 5000 символов' }]}
          >
            <Input.TextArea
              rows={10}
              placeholder="Введите базовый текст гороскопа для этого знака..."
              showCount
              maxLength={5000}
            />
          </Form.Item>

          <Form.Item name="notes" label="Заметки (видны только админам)">
            <Input.TextArea rows={3} placeholder="Внутренние заметки..." />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
