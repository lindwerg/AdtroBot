import { api } from '@/api/client'

export interface PromoCodeListItem {
  id: number
  code: string
  discount_percent: number
  valid_from: string
  valid_until: string | null
  max_uses: number | null
  current_uses: number
  partner_id: number | null
  partner_commission_percent: number | null
  is_active: boolean
  created_at: string
}

export interface PromoCodeListResponse {
  items: PromoCodeListItem[]
  total: number
  page: number
  page_size: number
}

export interface CreatePromoCodeRequest {
  code: string
  discount_percent: number
  valid_until?: string
  max_uses?: number
  partner_id?: number
  partner_commission_percent?: number
}

export async function getPromoCodes(params: Record<string, unknown> = {}): Promise<PromoCodeListResponse> {
  const { data } = await api.get<PromoCodeListResponse>('/promo-codes', { params })
  return data
}

export async function createPromoCode(request: CreatePromoCodeRequest): Promise<PromoCodeListItem> {
  const { data } = await api.post<PromoCodeListItem>('/promo-codes', request)
  return data
}

export async function updatePromoCode(id: number, request: Partial<CreatePromoCodeRequest & { is_active: boolean }>): Promise<void> {
  await api.patch(`/promo-codes/${id}`, request)
}

export async function deletePromoCode(id: number): Promise<void> {
  await api.delete(`/promo-codes/${id}`)
}
