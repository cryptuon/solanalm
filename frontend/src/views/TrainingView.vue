<script setup lang="ts">
import { ref, onMounted } from 'vue';
import api from '@/services/api';

const training = ref<any>(null);
const loading = ref(false);

const fetchTraining = async () => {
  loading.value = true;
  try {
    const response = await api.get('/api/v1/node/training/current');
    training.value = response.data;
  } catch (e) {
    // Not a training node
    training.value = { active: false };
  } finally {
    loading.value = false;
  }
};

onMounted(fetchTraining);
</script>

<template>
  <div class="space-y-6 mt-16">
    <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Federated Learning</h1>

    <div v-if="training?.active" class="card p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Current Training Round</h2>

      <div class="space-y-4">
        <div class="flex justify-between">
          <span class="text-gray-500 dark:text-gray-400">Round ID</span>
          <span class="font-mono text-gray-900 dark:text-white">{{ training.round?.round_id?.slice(0, 12) }}...</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500 dark:text-gray-400">Model</span>
          <span class="text-gray-900 dark:text-white">{{ training.round?.model }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-500 dark:text-gray-400">Status</span>
          <span class="text-gray-900 dark:text-white capitalize">{{ training.round?.status }}</span>
        </div>

        <!-- Progress -->
        <div>
          <div class="flex justify-between text-sm mb-2">
            <span class="text-gray-500 dark:text-gray-400">Progress</span>
            <span class="text-gray-900 dark:text-white">{{ ((training.round?.progress ?? 0) * 100).toFixed(1) }}%</span>
          </div>
          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
            <div
              class="bg-solana-purple h-4 rounded-full transition-all"
              :style="{ width: `${(training.round?.progress ?? 0) * 100}%` }"
            ></div>
          </div>
        </div>

        <div v-if="training.round?.current_loss" class="flex justify-between">
          <span class="text-gray-500 dark:text-gray-400">Current Loss</span>
          <span class="text-gray-900 dark:text-white">{{ training.round.current_loss.toFixed(4) }}</span>
        </div>

        <div class="flex justify-between">
          <span class="text-gray-500 dark:text-gray-400">Expected Reward</span>
          <span class="text-solana-green font-bold">{{ (training.round?.expected_reward ?? 0).toFixed(4) }} SOL</span>
        </div>
      </div>
    </div>

    <div v-else class="card p-6 text-center">
      <div class="py-12">
        <svg class="w-16 h-16 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h3 class="mt-4 text-lg font-medium text-gray-900 dark:text-white">No Active Training</h3>
        <p class="mt-2 text-gray-500 dark:text-gray-400">
          This node is not currently participating in any training rounds.
        </p>
      </div>
    </div>
  </div>
</template>
