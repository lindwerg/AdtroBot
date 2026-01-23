import { api } from '@/api/client'

export interface HoroscopeContentItem {
  id: number
  zodiac_sign: string
  base_text: string
  notes: string | null
  updated_at: string
}

export interface HoroscopeContentListResponse {
  items: HoroscopeContentItem[]
}

export interface UpdateHoroscopeContentRequest {
  base_text: string
  notes?: string | null
}

export async function getHoroscopeContent(): Promise<HoroscopeContentListResponse> {
  const { data } = await api.get<HoroscopeContentListResponse>('/content/horoscopes')
  return data
}

export async function updateHoroscopeContent(
  zodiacSign: string,
  request: UpdateHoroscopeContentRequest
): Promise<HoroscopeContentItem> {
  const { data } = await api.put<HoroscopeContentItem>(
    `/content/horoscopes/${zodiacSign}`,
    request
  )
  return data
}
