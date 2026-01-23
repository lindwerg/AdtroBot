import { api } from '@/api/client'

export interface PaymentListItem {
  id: string
  user_id: number
  subscription_id: number | null
  amount: number
  currency: string
  status: string
  is_recurring: boolean
  description: string | null
  created_at: string
  paid_at: string | null
  user_telegram_id: number | null
  user_username: string | null
}

export interface PaymentListResponse {
  items: PaymentListItem[]
  total: number
  page: number
  page_size: number
  total_amount: number
}

export interface SubscriptionListItem {
  id: number
  user_id: number
  plan: string
  status: string
  payment_method_id: string | null
  started_at: string
  current_period_start: string
  current_period_end: string
  canceled_at: string | null
  created_at: string
  user_telegram_id: number | null
  user_username: string | null
}

export interface SubscriptionListResponse {
  items: SubscriptionListItem[]
  total: number
  page: number
  page_size: number
}

export async function getPayments(params: Record<string, unknown> = {}): Promise<PaymentListResponse> {
  const { data } = await api.get<PaymentListResponse>('/payments', { params })
  return data
}

export async function getSubscriptions(params: Record<string, unknown> = {}): Promise<SubscriptionListResponse> {
  const { data } = await api.get<SubscriptionListResponse>('/subscriptions', { params })
  return data
}

export async function updateSubscriptionStatus(id: number, status: string): Promise<void> {
  await api.patch(`/subscriptions/${id}`, { status })
}
