import { api } from '@/api/client'

export interface ExperimentListItem {
  id: number
  name: string
  description: string | null
  metric: string
  variant_b_percent: number
  status: string
  started_at: string | null
  ended_at: string | null
  created_at: string
}

export interface ExperimentVariantStats {
  variant: string
  users: number
  conversions: number
  conversion_rate: number
}

export interface ExperimentResults {
  experiment: ExperimentListItem
  variant_a: ExperimentVariantStats
  variant_b: ExperimentVariantStats
  winner: string | null
}

export interface UTMSourceStats {
  source: string
  users: number
  premium_users: number
  conversion_rate: number
  total_revenue: number
}

export interface UTMAnalyticsResponse {
  sources: UTMSourceStats[]
  total_users: number
}

export interface ExperimentListResponse {
  items: ExperimentListItem[]
  total: number
  page: number
  page_size: number
}

export async function getExperiments(
  page = 1,
  pageSize = 20
): Promise<ExperimentListResponse> {
  const { data } = await api.get<ExperimentListResponse>('/experiments', {
    params: { page, page_size: pageSize },
  })
  return data
}

export async function createExperiment(request: {
  name: string
  description?: string
  metric: string
  variant_b_percent?: number
}): Promise<ExperimentListItem> {
  const { data } = await api.post<ExperimentListItem>('/experiments', request)
  return data
}

export async function startExperiment(id: number): Promise<void> {
  await api.post(`/experiments/${id}/start`)
}

export async function stopExperiment(id: number): Promise<void> {
  await api.post(`/experiments/${id}/stop`)
}

export async function getExperimentResults(
  id: number
): Promise<ExperimentResults> {
  const { data } = await api.get<ExperimentResults>(`/experiments/${id}/results`)
  return data
}

export async function getUTMAnalytics(): Promise<UTMAnalyticsResponse> {
  const { data } = await api.get<UTMAnalyticsResponse>('/utm-analytics')
  return data
}
