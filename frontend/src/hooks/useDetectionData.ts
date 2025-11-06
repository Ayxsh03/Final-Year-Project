// import { useQuery } from '@tanstack/react-query';
// import { apiService } from '@/services/api';

// export const useDashboardStats = () => {
//   return useQuery({
//     queryKey: ['dashboard-stats'],
//     queryFn: () => apiService.getDashboardStats(),
//     refetchInterval: 3000, // Refresh every 30 seconds
//   });
// };

// export const useDetectionEvents = (page = 1, limit = 10, search?: string) => {
//   return useQuery({
//     queryKey: ['detection-events', page, limit, search],
//     queryFn: () => apiService.getDetectionEvents(page, limit, search),
//     refetchInterval: 1000, // Refresh every 1 seconds
//   });
// };

// export const useHourlyData = () => {
//   return useQuery({
//     queryKey: ['hourly-data'],
//     queryFn: () => apiService.getHourlyData(),
//     refetchInterval: 60000, // Refresh every minute
//   });
// };

// export const useCameras = () => {
//   return useQuery({
//     queryKey: ['cameras'],
//     queryFn: () => apiService.getCameras(),
//     refetchInterval: 15000, // Refresh every 15 seconds
//   });
// };

// export const useTrends = () => {
//   return useQuery({
//     queryKey: ['trends'],
//     queryFn: () => apiService.getTrends(),
//     refetchInterval: 300000, // Refresh every 5 minutes
//   });
// };

import { useQuery } from '@tanstack/react-query';
import { apiService } from '@/services/api';

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiService.getDashboardStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useDetectionEvents = (
  page = 1, 
  limit = 10, 
  search?: string,
  dateFilter?: string,
  confidenceFilter?: string
) => {
  return useQuery({
    queryKey: ['detection-events', page, limit, search, dateFilter, confidenceFilter],
    queryFn: () => apiService.getDetectionEvents(page, limit, search, dateFilter, confidenceFilter),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
};

export const useHourlyData = () => {
  return useQuery({
    queryKey: ['hourly-data'],
    queryFn: () => apiService.getHourlyData(),
    refetchInterval: 60000, // Refresh every minute
  });
};

export const useCameras = () => {
  return useQuery({
    queryKey: ['cameras'],
    queryFn: () => apiService.getCameras(),
    refetchInterval: 15000, // Refresh every 15 seconds
  });
};

export const useTrends = () => {
  return useQuery({
    queryKey: ['trends'],
    queryFn: () => apiService.getTrends(),
    refetchInterval: 300000, // Refresh every 5 minutes
  });
};

export const usePeopleCount = (search?: string) => {
  return useQuery({
    queryKey: ['people-count', search],
    queryFn: () => apiService.getPeopleCount(search),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
};

export const useAIIntelligenceMetrics = () => {
  return useQuery({
    queryKey: ['ai-intelligence-metrics'],
    queryFn: () => apiService.getAIIntelligenceMetrics(),
    refetchInterval: 60000, // Refresh every minute
  });
};