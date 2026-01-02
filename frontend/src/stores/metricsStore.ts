import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/services/api';

interface Stats {
  requests_served: number;
  requests_succeeded: number;
  requests_failed: number;
  total_tokens_generated: number;
  average_response_time: number;
  success_rate: number;
  total_earnings_sol: number;
  pending_earnings_sol: number;
  uptime_seconds: number;
  requests_last_hour: number;
  requests_last_24h: number;
}

export const useMetricsStore = defineStore('metrics', () => {
  const stats = ref<Stats | null>(null);
  const requestHistory = ref<any[]>([]);
  const loading = ref(false);

  const successRate = computed(() => {
    return stats.value?.success_rate ?? 1.0;
  });

  const totalRequests = computed(() => {
    return stats.value?.requests_served ?? 0;
  });

  const totalEarnings = computed(() => {
    return stats.value?.total_earnings_sol ?? 0;
  });

  async function fetchStats() {
    loading.value = true;
    try {
      const response = await api.get('/api/v1/node/stats');
      stats.value = response.data;
    } catch (e) {
      console.error('Failed to fetch stats:', e);
    } finally {
      loading.value = false;
    }
  }

  async function fetchEarningsSummary() {
    try {
      const response = await api.get('/api/v1/node/stats/earnings/summary');
      return response.data;
    } catch (e) {
      console.error('Failed to fetch earnings:', e);
      return null;
    }
  }

  function updateFromWebSocket(data: Partial<Stats>) {
    if (stats.value) {
      stats.value = { ...stats.value, ...data };
    } else {
      stats.value = data as Stats;
    }
  }

  return {
    stats,
    requestHistory,
    loading,
    successRate,
    totalRequests,
    totalEarnings,
    fetchStats,
    fetchEarningsSummary,
    updateFromWebSocket,
  };
});
