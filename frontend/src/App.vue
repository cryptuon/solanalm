<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useSettingsStore } from '@/stores/settingsStore';
import { useWebSocketStore } from '@/stores/websocketStore';
import AppHeader from '@/components/common/AppHeader.vue';
import AppSidebar from '@/components/common/AppSidebar.vue';

const settingsStore = useSettingsStore();
const wsStore = useWebSocketStore();

onMounted(async () => {
  // Load settings
  settingsStore.loadSettings();

  // Apply dark mode
  if (settingsStore.darkMode) {
    document.documentElement.classList.add('dark');
  }

  // Connect WebSocket
  await wsStore.connect();
});

onUnmounted(() => {
  wsStore.disconnect();
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <AppHeader />
    <div class="flex">
      <AppSidebar />
      <main class="flex-1 p-6 ml-64">
        <router-view />
      </main>
    </div>
  </div>
</template>
