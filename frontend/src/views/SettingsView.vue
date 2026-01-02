<script setup lang="ts">
import { useSettingsStore } from '@/stores/settingsStore';
import { useNodeStore } from '@/stores/nodeStore';

const settingsStore = useSettingsStore();
const nodeStore = useNodeStore();
</script>

<template>
  <div class="space-y-6 mt-16">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Settings</h1>

    <!-- Appearance -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Appearance</h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-900 dark:text-white font-medium">Dark Mode</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">Use dark theme for the dashboard</p>
          </div>
          <button
            @click="settingsStore.toggleDarkMode"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
              settingsStore.darkMode ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
            ]"
          >
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                settingsStore.darkMode ? 'translate-x-6' : 'translate-x-1'
              ]"
            />
          </button>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-gray-900 dark:text-white font-medium">Compact View</p>
            <p class="text-sm text-gray-500 dark:text-gray-400">Use smaller components</p>
          </div>
          <button
            @click="settingsStore.compactView = !settingsStore.compactView; settingsStore.saveSettings()"
            :class="[
              'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
              settingsStore.compactView ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'
            ]"
          >
            <span
              :class="[
                'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                settingsStore.compactView ? 'translate-x-6' : 'translate-x-1'
              ]"
            />
          </button>
        </div>
      </div>
    </div>

    <!-- Node Info -->
    <div class="card p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Node Information</h2>
      <dl class="space-y-3">
        <div class="flex justify-between">
          <dt class="text-gray-500 dark:text-gray-400">Node ID</dt>
          <dd class="font-mono text-gray-900 dark:text-white">{{ nodeStore.info?.node_id }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500 dark:text-gray-400">Wallet</dt>
          <dd class="font-mono text-gray-900 dark:text-white">{{ nodeStore.info?.wallet_address }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500 dark:text-gray-400">Endpoint</dt>
          <dd class="font-mono text-gray-900 dark:text-white">{{ nodeStore.info?.endpoint_url }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500 dark:text-gray-400">Gateway</dt>
          <dd class="font-mono text-gray-900 dark:text-white">{{ nodeStore.info?.gateway_url ?? 'Not connected' }}</dd>
        </div>
      </dl>
    </div>
  </div>
</template>
