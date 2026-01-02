<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useNodeStore } from '@/stores/nodeStore';

const nodeStore = useNodeStore();

let refreshInterval: number | null = null;

onMounted(async () => {
  await nodeStore.fetchHardware();

  refreshInterval = window.setInterval(async () => {
    await nodeStore.fetchHardware();
  }, 2000);
});

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval);
});
</script>

<template>
  <div class="space-y-6 mt-16">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Hardware Monitoring</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- CPU -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">CPU</h2>
        <div class="space-y-4">
          <div class="text-center">
            <div class="text-5xl font-bold text-primary-500">
              {{ nodeStore.hardware?.cpu?.percent ?? 0 }}%
            </div>
            <p class="text-gray-500 dark:text-gray-400 mt-2">
              {{ nodeStore.hardware?.cpu?.cores ?? 0 }} cores
            </p>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <div
              class="bg-primary-500 h-4 rounded-full transition-all"
              :style="{ width: `${nodeStore.hardware?.cpu?.percent ?? 0}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- Memory -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Memory</h2>
        <div class="space-y-4">
          <div class="text-center">
            <div class="text-5xl font-bold text-primary-500">
              {{ nodeStore.hardware?.memory?.percent ?? 0 }}%
            </div>
            <p class="text-gray-500 dark:text-gray-400 mt-2">
              {{ nodeStore.hardware?.memory?.used_gb?.toFixed(1) ?? 0 }} / {{ nodeStore.hardware?.memory?.total_gb?.toFixed(1) ?? 0 }} GB
            </p>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <div
              class="bg-primary-500 h-4 rounded-full transition-all"
              :style="{ width: `${nodeStore.hardware?.memory?.percent ?? 0}%` }"
            ></div>
          </div>
        </div>
      </div>

      <!-- GPU -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">GPU</h2>
        <div v-if="nodeStore.hardware?.gpu?.available" class="space-y-4">
          <div class="text-center">
            <div class="text-5xl font-bold text-solana-purple">
              {{ nodeStore.hardware?.gpu?.percent ?? 0 }}%
            </div>
            <p class="text-gray-500 dark:text-gray-400 mt-2">
              {{ nodeStore.hardware?.gpu?.memory_used_gb?.toFixed(1) ?? 0 }} / {{ nodeStore.hardware?.gpu?.memory_total_gb?.toFixed(1) ?? 0 }} GB VRAM
            </p>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <div
              class="bg-solana-purple h-4 rounded-full transition-all"
              :style="{ width: `${nodeStore.hardware?.gpu?.percent ?? 0}%` }"
            ></div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
          No GPU detected
        </div>
      </div>

      <!-- Storage -->
      <div class="card p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Storage</h2>
        <div class="space-y-4">
          <div class="text-center">
            <div class="text-5xl font-bold text-solana-green">
              {{ nodeStore.hardware?.storage?.percent ?? 0 }}%
            </div>
            <p class="text-gray-500 dark:text-gray-400 mt-2">
              Used
            </p>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <div
              class="bg-solana-green h-4 rounded-full transition-all"
              :style="{ width: `${nodeStore.hardware?.storage?.percent ?? 0}%` }"
            ></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
