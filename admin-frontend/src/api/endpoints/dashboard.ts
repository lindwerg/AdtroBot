import { api } from '@/api/client'

export interface SparklinePoint {
  date: string
  value: number
}

export interface KPIMetric {
  value: number | string
  trend: number
  sparkline: SparklinePoint[]
}

export interface DashboardMetrics {
  active_users_dau: KPIMetric
  active_users_mau: KPIMetric
  new_users_today: KPIMetric
  retention_d7: KPIMetric
  horoscopes_today: KPIMetric
  tarot_spreads_today: KPIMetric
  most_active_zodiac: string
  revenue_today: KPIMetric
  revenue_month: KPIMetric
  conversion_rate: KPIMetric
  arpu: KPIMetric
  error_rate: KPIMetric | null
  avg_response_time: KPIMetric | null
  api_costs_today: KPIMetric | null
  api_costs_month: KPIMetric | null
}

export interface FunnelStage {
  name: string
  name_ru: string
  value: number
  conversion_from_prev: number | null
  dropoff_count: number | null
  dropoff_percent: number | null
}

export interface FunnelData {
  stages: FunnelStage[]
  period_days: number
}

export async function getDashboardMetrics(): Promise<DashboardMetrics> {
  const { data } = await api.get<DashboardMetrics>('/dashboard')
  return data
}

export async function getFunnelData(days: number = 30): Promise<FunnelData> {
  const { data } = await api.get<FunnelData>('/funnel', { params: { days } })
  return data
}
