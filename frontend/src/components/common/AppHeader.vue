<script setup lang="ts">
import { computed } from 'vue';
import { useNodeStore } from '@/stores/nodeStore';
import { useSettingsStore } from '@/stores/settingsStore';
import { useWebSocketStore } from '@/stores/websocketStore';

const nodeStore = useNodeStore();
const settingsStore = useSettingsStore();
const wsStore = useWebSocketStore();

const statusClass = computed(() => {
  if (!nodeStore.isOnline) return 'bg-red-500';
  if (nodeStore.isPaused) return 'bg-yellow-500';
  return 'bg-green-500';
});

const statusText = computed(() => {
  if (!nodeStore.isOnline) return 'Offline';
  if (nodeStore.isPaused) return 'Paused';
  return 'Online';
});
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 z-50">
    <div class="flex items-center justify-between h-full px-6">
      <!-- Logo and title -->
      <div class="flex items-center space-x-4">
        <div class="flex items-center space-x-2">
          <span class="text-2xl font-bold bg-gradient-to-r from-solana-purple to-solana-green bg-clip-text text-transparent">
            SolanaLM
          </span>
          <span class="text-gray-500 dark:text-gray-400">Dashboard</span>
        </div>
      </div>

      <!-- Status indicators -->
      <div class="flex items-center space-x-6">
        <!-- Node status -->
        <div class="flex items-center space-x-2">
          <div :class="['w-3 h-3 rounded-full', statusClass]"></div>
          <span class="text-sm text-gray-600 dark:text-gray-300">{{ statusText }}</span>
        </div>

        <!-- WebSocket status -->
        <div class="flex items-center space-x-2">
          <div :class="['w-2 h-2 rounded-full', wsStore.isConnected ? 'bg-green-500' : 'bg-red-500']"></div>
          <span class="text-xs text-gray-500">{{ wsStore.isConnected ? 'Live' : 'Disconnected' }}</span>
        </div>

        <!-- Node ID -->
        <div v-if="nodeStore.info" class="text-sm text-gray-500 dark:text-gray-400 font-mono">
          {{ nodeStore.info.node_id.slice(0, 12) }}...
        </div>

        <!-- Dark mode toggle -->
        <button
          @click="settingsStore.toggleDarkMode"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <svg v-if="settingsStore.darkMode" class="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
          </svg>
          <svg v-else class="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
          </svg>
        </button>
      </div>
    </div>
  </header>
</template>
