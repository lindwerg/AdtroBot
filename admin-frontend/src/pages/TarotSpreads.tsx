import { useState } from 'react'
import {
  Card, Table, Input, Select, Button, Modal, Tag,
  Typography, Descriptions, Space, Row, Col, Divider
} from 'antd'
import { EyeOutlined, SearchOutlined, UserOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { getSpreads, getSpreadDetail, type TarotSpreadListItem } from '@/api/endpoints/spreads'

const SPREAD_TYPE_LABELS: Record<string, string> = {
  three_card: '3 карты',
  celtic_cross: 'Кельтский крест',
  card_of_day: 'Карта дня',
}

export default function TarotSpreadsPage() {
  const [filters, setFilters] = useState<{
    search?: string
    spread_type?: string
    page: number
  }>({ page: 1 })
  const [detailModal, setDetailModal] = useState<{ open: boolean; id: number | null }>({
    open: false,
    id: null,
  })

  const { data, isLoading } = useQuery({
    queryKey: ['tarot-spreads', filters],
    queryFn: () => getSpreads({
      page: filters.page,
      page_size: 20,
      search: filters.search,
      spread_type: filters.spread_type,
    }),
  })

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ['spread-detail', detailModal.id],
    queryFn: () => getSpreadDetail(detailModal.id!),
    enabled: detailModal.id !== null,
  })

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 60,
    },
    {
      title: 'Пользователь',
      key: 'user',
      width: 150,
      render: (_: unknown, r: TarotSpreadListItem) => (
        <Space>
          <UserOutlined />
          {r.username || `ID: ${r.telegram_id}`}
        </Space>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'spread_type',
      width: 130,
      render: (v: string) => (
        <Tag color={v === 'celtic_cross' ? 'gold' : 'blue'}>
          {SPREAD_TYPE_LABELS[v] || v}
        </Tag>
      ),
    },
    {
      title: 'Вопрос',
      dataIndex: 'question',
      ellipsis: true,
    },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      width: 140,
      render: (v: string) => dayjs(v).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 100,
      render: (_: unknown, r: TarotSpreadListItem) => (
        <Button
          size="small"
          icon={<EyeOutlined />}
          onClick={() => setDetailModal({ open: true, id: r.id })}
        >
          Детали
        </Button>
      ),
    },
  ]

  return (
    <>
      <Card
        title="Расклады таро"
        extra={
          <Space>
            <Input
              placeholder="Поиск по вопросу..."
              prefix={<SearchOutlined />}
              style={{ width: 200 }}
              allowClear
              onChange={(e) => setFilters({ ...filters, search: e.target.value, page: 1 })}
            />
            <Select
              placeholder="Тип расклада"
              style={{ width: 150 }}
              allowClear
              onChange={(v) => setFilters({ ...filters, spread_type: v, page: 1 })}
              options={[
                { value: 'three_card', label: '3 карты' },
                { value: 'celtic_cross', label: 'Кельтский крест' },
                { value: 'card_of_day', label: 'Карта дня' },
              ]}
            />
          </Space>
        }
      >
        <Table
          dataSource={data?.items}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: filters.page,
            total: data?.total,
            pageSize: 20,
            onChange: (page) => setFilters({ ...filters, page }),
            showTotal: (total) => `Всего: ${total}`,
          }}
        />
      </Card>

      <Modal
        title={`Расклад #${detailModal.id}`}
        open={detailModal.open}
        onCancel={() => setDetailModal({ open: false, id: null })}
        footer={null}
        width={800}
      >
        {detailLoading && <Typography.Text>Загрузка...</Typography.Text>}
        {detail && (
          <>
            <Descriptions bordered size="small" column={2}>
              <Descriptions.Item label="Пользователь">
                {detail.username || `Telegram ID: ${detail.telegram_id}`}
              </Descriptions.Item>
              <Descriptions.Item label="Тип расклада">
                <Tag color={detail.spread_type === 'celtic_cross' ? 'gold' : 'blue'}>
                  {SPREAD_TYPE_LABELS[detail.spread_type] || detail.spread_type}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Дата" span={2}>
                {dayjs(detail.created_at).format('DD.MM.YYYY HH:mm')}
              </Descriptions.Item>
              <Descriptions.Item label="Вопрос" span={2}>
                <Typography.Text strong>{detail.question}</Typography.Text>
              </Descriptions.Item>
            </Descriptions>

            <Divider>Карты</Divider>
            <Row gutter={[8, 8]}>
              {detail.cards.map((card) => (
                <Col key={card.position} xs={12} sm={8} md={6}>
                  <Card size="small">
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {card.position_name}
                    </Typography.Text>
                    <br />
                    <Typography.Text strong>
                      {card.card_name}
                    </Typography.Text>
                    {card.is_reversed && (
                      <Tag color="orange" style={{ marginLeft: 4 }}>
                        перевернута
                      </Tag>
                    )}
                  </Card>
                </Col>
              ))}
            </Row>

            {detail.interpretation && (
              <>
                <Divider>Интерпретация</Divider>
                <Card size="small" style={{ maxHeight: 300, overflow: 'auto' }}>
                  <Typography.Paragraph
                    style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}
                  >
                    {detail.interpretation}
                  </Typography.Paragraph>
                </Card>
              </>
            )}
          </>
        )}
      </Modal>
    </>
  )
}
