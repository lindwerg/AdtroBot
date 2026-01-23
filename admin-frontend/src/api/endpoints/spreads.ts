import { api } from '@/api/client'

export interface TarotSpreadListItem {
  id: number
  user_id: number
  telegram_id: number | null
  username: string | null
  spread_type: string
  question: string
  created_at: string
}

export interface TarotSpreadListResponse {
  items: TarotSpreadListItem[]
  total: number
  page: number
  page_size: number
}

export interface CardPosition {
  position: number
  position_name: string
  card_name: string
  is_reversed: boolean
}

export interface TarotSpreadDetail {
  id: number
  user_id: number
  telegram_id: number | null
  username: string | null
  spread_type: string
  question: string
  cards: CardPosition[]
  interpretation: string | null
  created_at: string
}

export interface SpreadsParams {
  page?: number
  page_size?: number
  user_id?: number
  search?: string
  spread_type?: string
  date_from?: string
  date_to?: string
}

export async function getSpreads(params: SpreadsParams = {}): Promise<TarotSpreadListResponse> {
  const { data } = await api.get<TarotSpreadListResponse>('/tarot-spreads', { params })
  return data
}

export async function getSpreadDetail(spreadId: number): Promise<TarotSpreadDetail> {
  const { data } = await api.get<TarotSpreadDetail>(`/tarot-spreads/${spreadId}`)
  return data
}
