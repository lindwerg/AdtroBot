import { useQuery } from '@tanstack/react-query'
import { getDashboardMetrics, getFunnelData } from '@/api/endpoints/dashboard'
import type { DashboardMetrics, FunnelData } from '@/api/endpoints/dashboard'

export function useDashboardMetrics() {
  return useQuery<DashboardMetrics>({
    queryKey: ['dashboard'],
    queryFn: getDashboardMetrics,
    refetchInterval: 60000, // Refresh every minute
  })
}

export function useFunnelData(days: number = 30) {
  return useQuery<FunnelData>({
    queryKey: ['funnel', days],
    queryFn: () => getFunnelData(days),
  })
}
