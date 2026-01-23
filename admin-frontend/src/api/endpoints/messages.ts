import { api } from '@/api/client'

export interface SendMessageRequest {
  text: string
  target_user_id?: number
  filters?: Record<string, unknown>
  scheduled_at?: string
}

export interface SendMessageResponse {
  message_id: number
  status: string
  recipients_count: number
}

export interface MessageHistoryItem {
  id: number
  text: string
  filters: Record<string, unknown>
  target_user_id: number | null
  scheduled_at: string | null
  sent_at: string | null
  total_recipients: number
  delivered_count: number
  failed_count: number
  status: string
  created_at: string
}

export interface MessageHistoryResponse {
  items: MessageHistoryItem[]
  total: number
  page: number
  page_size: number
}

export async function sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
  const { data } = await api.post<SendMessageResponse>('/messages', request)
  return data
}

export async function getMessageHistory(page = 1, pageSize = 20): Promise<MessageHistoryResponse> {
  const { data } = await api.get<MessageHistoryResponse>('/messages', {
    params: { page, page_size: pageSize },
  })
  return data
}

export async function cancelMessage(messageId: number): Promise<void> {
  await api.delete(`/messages/${messageId}`)
}
