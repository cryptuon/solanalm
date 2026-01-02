<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import api from '@/services/api';

const logs = ref<any[]>([]);
const loading = ref(false);
const levelFilter = ref('');
const searchQuery = ref('');

let refreshInterval: number | null = null;

const fetchLogs = async () => {
  loading.value = true;
  try {
    const params: any = { limit: 200 };
    if (levelFilter.value) params.level = levelFilter.value;
    if (searchQuery.value) params.search = searchQuery.value;

    const response = await api.get('/api/v1/node/logs', { params });
    logs.value = response.data.logs;
  } catch (e) {
    console.error('Failed to fetch logs:', e);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchLogs();
  refreshInterval = window.setInterval(fetchLogs, 5000);
});

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});

const levelColor = (level: string): string => {
  switch (level) {
    case 'ERROR': return 'text-red-500';
    case 'WARNING': return 'text-yellow-500';
    case 'INFO': return 'text-blue-500';
    case 'DEBUG': return 'text-gray-500';
    default: return 'text-gray-500';
  }
};

const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleTimeString();
};
</script>

<template>
  <div class="space-y-6 mt-16">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Logs</h1>
      <button @click="fetchLogs" class="btn btn-secondary">Refresh</button>
    </div>

    <!-- Filters -->
    <div class="flex space-x-4">
      <input
        v-model="searchQuery"
        @input="fetchLogs"
        type="text"
        placeholder="Search logs..."
        class="input w-64"
      />
      <select v-model="levelFilter" @change="fetchLogs" class="input w-40">
        <option value="">All Levels</option>
        <option value="DEBUG">DEBUG</option>
        <option value="INFO">INFO</option>
        <option value="WARNING">WARNING</option>
        <option value="ERROR">ERROR</option>
      </select>
    </div>

    <!-- Log entries -->
    <div class="card overflow-hidden">
      <div class="bg-gray-50 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700 text-sm text-gray-500">
        {{ logs.length }} entries
      </div>
      <div class="divide-y divide-gray-100 dark:divide-gray-700 max-h-[600px] overflow-y-auto font-mono text-sm">
        <div
          v-for="(log, index) in logs"
          :key="index"
          class="px-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          <div class="flex items-start space-x-4">
            <span class="text-gray-400 w-20 flex-shrink-0">{{ formatTime(log.timestamp) }}</span>
            <span :class="['w-16 flex-shrink-0 font-medium', levelColor(log.level)]">{{ log.level }}</span>
            <span class="text-gray-500 w-32 flex-shrink-0">{{ log.source }}</span>
            <span class="text-gray-900 dark:text-white flex-1">{{ log.message }}</span>
          </div>
        </div>
        <div v-if="logs.length === 0" class="p-8 text-center text-gray-500">
          No logs found
        </div>
      </div>
    </div>
  </div>
</template>
