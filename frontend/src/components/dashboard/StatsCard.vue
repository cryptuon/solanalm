<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: number;
  icon?: string;
}>();

const trendClass = computed(() => {
  if (!props.trend) return '';
  return props.trend > 0 ? 'text-green-500' : 'text-red-500';
});

const trendIcon = computed(() => {
  if (!props.trend) return '';
  return props.trend > 0 ? '↑' : '↓';
});
</script>

<template>
  <div class="stat-card">
    <div class="flex items-start justify-between">
      <div>
        <p class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ title }}</p>
        <p class="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{{ value }}</p>
        <p v-if="subtitle" class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ subtitle }}</p>
      </div>
      <div v-if="trend" :class="['text-sm font-medium', trendClass]">
        {{ trendIcon }} {{ Math.abs(trend) }}%
      </div>
    </div>
  </div>
</template>
