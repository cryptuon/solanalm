<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMetricsStore } from '@/stores/metricsStore';

const metricsStore = useMetricsStore();
const earnings = ref<any>(null);

onMounted(async () => {
  await metricsStore.fetchStats();
  earnings.value = await metricsStore.fetchEarningsSummary();
});

const formatSOL = (sol: number): string => {
  return sol?.toFixed(4) ?? '0.0000';
};
</script>

<template>
  <div class="space-y-6 mt-16">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Earnings</h1>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="card p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">Total Earned</p>
        <p class="text-3xl font-bold text-solana-green mt-2">
          {{ formatSOL(earnings?.total_earned ?? metricsStore.stats?.total_earnings_sol ?? 0) }} SOL
        </p>
      </div>
      <div class="card p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">Today</p>
        <p class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
          {{ formatSOL(earnings?.today ?? 0) }} SOL
        </p>
      </div>
      <div class="card p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">This Week</p>
        <p class="text-3xl font-bold text-gray-900 dark:text-white mt-2">
          {{ formatSOL(earnings?.this_week ?? 0) }} SOL
        </p>
      </div>
      <div class="card p-6">
        <p class="text-sm text-gray-500 dark:text-gray-400">Pending</p>
        <p class="text-3xl font-bold text-yellow-500 mt-2">
          {{ formatSOL(earnings?.pending ?? metricsStore.stats?.pending_earnings_sol ?? 0) }} SOL
        </p>
      </div>
    </div>

    <!-- Breakdown -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Revenue Breakdown</h2>
      <div class="grid grid-cols-2 gap-6">
        <div>
          <p class="text-sm text-gray-500 dark:text-gray-400">Inference Rewards</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {{ formatSOL(earnings?.breakdown?.inference ?? 0) }} SOL
          </p>
        </div>
        <div>
          <p class="text-sm text-gray-500 dark:text-gray-400">Training Rewards</p>
          <p class="text-2xl font-bold text-gray-900 dark:text-white mt-1">
            {{ formatSOL(earnings?.breakdown?.training ?? 0) }} SOL
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
