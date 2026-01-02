<script setup lang="ts">
import { onMounted, onUnmounted, computed } from 'vue';
import { useNodeStore } from '@/stores/nodeStore';
import { useMetricsStore } from '@/stores/metricsStore';
import StatsCard from '@/components/dashboard/StatsCard.vue';

const nodeStore = useNodeStore();
const metricsStore = useMetricsStore();

let refreshInterval: number | null = null;

onMounted(async () => {
  await Promise.all([
    nodeStore.fetchInfo(),
    nodeStore.fetchHealth(),
    nodeStore.fetchHardware(),
    nodeStore.fetchEvents(),
    metricsStore.fetchStats(),
  ]);

  // Auto-refresh every 5 seconds
  refreshInterval = window.setInterval(async () => {
    await metricsStore.fetchStats();
    await nodeStore.fetchHardware();
  }, 5000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});

const formatUptime = (seconds: number): string => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

const formatNumber = (num: number): string => {
  return num.toLocaleString();
};

const formatSOL = (sol: number): string => {
  return sol.toFixed(4);
};
</script>

<template>
  <div class="space-y-6 mt-16">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatsCard
        title="Total Requests"
        :value="formatNumber(metricsStore.stats?.requests_served ?? 0)"
        :subtitle="`${metricsStore.stats?.requests_last_24h ?? 0} in last 24h`"
      />
      <StatsCard
        title="Tokens Generated"
        :value="formatNumber(metricsStore.stats?.total_tokens_generated ?? 0)"
      />
      <StatsCard
        title="Success Rate"
        :value="`${((metricsStore.stats?.success_rate ?? 1) * 100).toFixed(1)}%`"
      />
      <StatsCard
        title="Total Earnings"
        :value="`${formatSOL(metricsStore.stats?.total_earnings_sol ?? 0)} SOL`"
      />
    </div>

    <!-- Second Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Node Info -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Node Information</h2>
        <dl class="space-y-3">
          <div class="flex justify-between">
            <dt class="text-gray-500 dark:text-gray-400">Node ID</dt>
            <dd class="font-mono text-gray-900 dark:text-white">{{ nodeStore.info?.node_id?.slice(0, 16) }}...</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500 dark:text-gray-400">Type</dt>
            <dd class="text-gray-900 dark:text-white capitalize">{{ nodeStore.info?.node_type }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500 dark:text-gray-400">Model</dt>
            <dd class="text-gray-900 dark:text-white">{{ nodeStore.health?.model }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500 dark:text-gray-400">Device</dt>
            <dd class="text-gray-900 dark:text-white">{{ nodeStore.health?.device }}</dd>
          </div>
          <div class="flex justify-between">
            <dt class="text-gray-500 dark:text-gray-400">Uptime</dt>
            <dd class="text-gray-900 dark:text-white">{{ formatUptime(metricsStore.stats?.uptime_seconds ?? 0) }}</dd>
          </div>
        </dl>
      </div>

      <!-- Hardware Metrics -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Hardware</h2>
        <div class="space-y-4">
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-500 dark:text-gray-400">CPU</span>
              <span class="text-gray-900 dark:text-white">{{ nodeStore.hardware?.cpu?.percent ?? 0 }}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="bg-primary-500 h-2 rounded-full transition-all"
                :style="{ width: `${nodeStore.hardware?.cpu?.percent ?? 0}%` }"
              ></div>
            </div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-500 dark:text-gray-400">Memory</span>
              <span class="text-gray-900 dark:text-white">{{ nodeStore.hardware?.memory?.percent ?? 0 }}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="bg-primary-500 h-2 rounded-full transition-all"
                :style="{ width: `${nodeStore.hardware?.memory?.percent ?? 0}%` }"
              ></div>
            </div>
          </div>
          <div v-if="nodeStore.hardware?.gpu?.available">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-500 dark:text-gray-400">GPU</span>
              <span class="text-gray-900 dark:text-white">{{ nodeStore.hardware?.gpu?.percent ?? 0 }}%</span>
            </div>
            <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                class="bg-solana-purple h-2 rounded-full transition-all"
                :style="{ width: `${nodeStore.hardware?.gpu?.percent ?? 0}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h2>
        <div class="space-y-3 max-h-64 overflow-y-auto">
          <div
            v-for="event in nodeStore.events.slice(0, 10)"
            :key="event.event_id"
            class="flex items-start space-x-3 text-sm"
          >
            <div
              :class="[
                'w-2 h-2 mt-1.5 rounded-full',
                event.severity === 'error' ? 'bg-red-500' :
                event.severity === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
              ]"
            ></div>
            <div>
              <p class="text-gray-900 dark:text-white">{{ event.title }}</p>
              <p class="text-gray-500 dark:text-gray-400 text-xs">
                {{ new Date(event.timestamp).toLocaleTimeString() }}
              </p>
            </div>
          </div>
          <div v-if="nodeStore.events.length === 0" class="text-gray-500 dark:text-gray-400 text-center py-4">
            No recent activity
          </div>
        </div>
      </div>
    </div>

    <!-- Controls -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Controls</h2>
      <div class="flex space-x-4">
        <button
          v-if="nodeStore.isPaused"
          @click="nodeStore.resumeNode()"
          class="btn btn-primary"
        >
          Resume Node
        </button>
        <button
          v-else
          @click="nodeStore.pauseNode()"
          class="btn btn-secondary"
        >
          Pause Node
        </button>
        <button
          @click="nodeStore.restartNode()"
          class="btn btn-secondary"
        >
          Restart Node
        </button>
      </div>
    </div>
  </div>
</template>
