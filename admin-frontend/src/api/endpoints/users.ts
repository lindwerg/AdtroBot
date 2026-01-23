import { api } from '@/api/client'

export interface UserListItem {
  id: number
  telegram_id: number
  username: string | null
  zodiac_sign: string | null
  is_premium: boolean
  premium_until: string | null
  created_at: string
  tarot_spread_count: number
  daily_spread_limit: number
  detailed_natal_purchased_at: string | null
}

export interface UserListResponse {
  items: UserListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface UserListParams {
  page?: number
  page_size?: number
  search?: string
  zodiac_sign?: string
  is_premium?: boolean
  has_detailed_natal?: boolean
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface PaymentHistoryItem {
  id: string
  amount: number
  status: string
  description: string | null
  created_at: string
  paid_at: string | null
}

export interface SubscriptionInfo {
  id: number
  plan: string
  status: string
  started_at: string
  current_period_end: string
  canceled_at: string | null
}

export interface TarotSpreadHistoryItem {
  id: number
  spread_type: string
  question: string
  created_at: string
}

export interface UserDetail {
  id: number
  telegram_id: number
  username: string | null
  birth_date: string | null
  zodiac_sign: string | null
  birth_time: string | null
  birth_city: string | null
  timezone: string | null
  notifications_enabled: boolean
  notification_hour: number | null
  is_premium: boolean
  premium_until: string | null
  daily_spread_limit: number
  tarot_spread_count: number
  detailed_natal_purchased_at: string | null
  created_at: string
  subscription: SubscriptionInfo | null
  payments: PaymentHistoryItem[]
  recent_spreads: TarotSpreadHistoryItem[]
}

export interface UpdateSubscriptionRequest {
  action: 'activate' | 'cancel' | 'extend'
  days?: number
}

export interface GiftRequest {
  gift_type: 'premium_days' | 'detailed_natal' | 'tarot_spreads'
  value: number
}

export interface BulkActionRequest {
  user_ids: number[]
  action: 'activate_premium' | 'cancel_premium' | 'ban' | 'unban' | 'gift_spreads'
  value?: number
}

export interface BulkActionResponse {
  success_count: number
  failed_count: number
  errors: string[]
}

export async function getUsers(params: UserListParams = {}): Promise<UserListResponse> {
  const { data } = await api.get<UserListResponse>('/users', { params })
  return data
}

export async function getUser(userId: number): Promise<UserDetail> {
  const { data } = await api.get<UserDetail>(`/users/${userId}`)
  return data
}

export async function updateSubscription(userId: number, request: UpdateSubscriptionRequest): Promise<void> {
  await api.patch(`/users/${userId}/subscription`, request)
}

export async function giftUser(userId: number, request: GiftRequest): Promise<void> {
  await api.post(`/users/${userId}/gift`, request)
}

export async function bulkAction(request: BulkActionRequest): Promise<BulkActionResponse> {
  const { data } = await api.post<BulkActionResponse>('/users/bulk', request)
  return data
}
