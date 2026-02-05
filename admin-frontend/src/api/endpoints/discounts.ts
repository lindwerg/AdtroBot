import { api } from '@/api/client'

export interface GlobalDiscountListItem {
  id: number
  name: string
  target_plan: string
  discount_percent: number
  active_from: string
  active_until: string | null
  is_active: boolean
  created_at: string
}

export interface GlobalDiscountListResponse {
  items: GlobalDiscountListItem[]
  total: number
  page: number
  page_size: number
}

export interface CreateGlobalDiscountRequest {
  name: string
  target_plan: 'monthly' | 'yearly' | 'all'
  discount_percent: number
  active_until?: string
}

export async function getGlobalDiscounts(
  params: Record<string, unknown> = {},
): Promise<GlobalDiscountListResponse> {
  const { data } = await api.get<GlobalDiscountListResponse>('/global-discounts', { params })
  return data
}

export async function createGlobalDiscount(
  request: CreateGlobalDiscountRequest,
): Promise<GlobalDiscountListItem> {
  const { data } = await api.post<GlobalDiscountListItem>('/global-discounts', request)
  return data
}

export async function updateGlobalDiscount(
  id: number,
  request: Partial<CreateGlobalDiscountRequest & { is_active: boolean }>,
): Promise<void> {
  await api.patch(`/global-discounts/${id}`, request)
}

export async function deleteGlobalDiscount(id: number): Promise<void> {
  await api.delete(`/global-discounts/${id}`)
}
