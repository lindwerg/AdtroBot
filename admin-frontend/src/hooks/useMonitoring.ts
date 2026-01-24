import { useQuery } from '@tanstack/react-query'
import { getMonitoringData } from '@/api/monitoring'
import type { TimeRange, MonitoringData } from '@/api/monitoring'

export function useMonitoringData(range: TimeRange = '7d') {
  return useQuery<MonitoringData>({
    queryKey: ['monitoring', range],
    queryFn: () => getMonitoringData(range),
    refetchInterval: 60_000, // Refresh every minute
  })
}
