import { api } from './client'

export type TimeRange = '24h' | '7d' | '30d'

export interface ActiveUsersMetrics {
  dau: number
  wau: number
  mau: number
}

export interface CostByOperation {
  operation: string
  cost: number
  tokens: number
  requests: number
}

export interface CostByDay {
  date: string
  cost: number
  tokens: number
}

export interface APICostsData {
  total_cost: number
  total_tokens: number
  total_requests: number
  by_operation: CostByOperation[]
  by_day: CostByDay[]
}

export interface UnitEconomicsData {
  total_cost: number
  active_users: number
  paying_users: number
  active_paying_users: number
  cost_per_active_user: number
  cost_per_paying_user: number
}

export interface ErrorStatsData {
  error_count: number
  error_rate: number
  avg_response_time_ms: number
}

export interface MonitoringData {
  range: string
  active_users: ActiveUsersMetrics
  api_costs: APICostsData
  unit_economics: UnitEconomicsData
  error_stats: ErrorStatsData
}

export async function getMonitoringData(range: TimeRange = '7d'): Promise<MonitoringData> {
  const response = await api.get<MonitoringData>(`/monitoring?range=${range}`)
  return response.data
}
