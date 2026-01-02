import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import api from '@/services/api';

interface NodeInfo {
  node_id: string;
  node_type: string;
  version: string;
  wallet_address: string;
  endpoint_url: string;
  gateway_url: string | null;
  uptime_seconds: number;
  supported_models: string[];
}

interface NodeHealth {
  status: string;
  is_ready: boolean;
  is_paused: boolean;
  model_loaded: boolean;
  gateway_connected: boolean;
  device: string;
  model: string;
}

interface HardwareMetrics {
  cpu: { percent: number; cores: number };
  memory: { percent: number; used_gb: number; total_gb: number };
  gpu: { available: boolean; percent: number | null; memory_used_gb: number | null };
  storage: { percent: number };
}

interface NodeEvent {
  event_id: string;
  timestamp: string;
  event_type: string;
  severity: string;
  title: string;
  description: string;
}

export const useNodeStore = defineStore('node', () => {
  const info = ref<NodeInfo | null>(null);
  const health = ref<NodeHealth | null>(null);
  const hardware = ref<HardwareMetrics | null>(null);
  const events = ref<NodeEvent[]>([]);
  const training = ref<any>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isOnline = computed(() => health.value?.status === 'healthy');
  const isPaused = computed(() => health.value?.is_paused ?? false);

  async function fetchInfo() {
    try {
      const response = await api.get('/api/v1/node/info');
      info.value = response.data;
    } catch (e: any) {
      error.value = e.message;
    }
  }

  async function fetchHealth() {
    try {
      const response = await api.get('/api/v1/node/health');
      health.value = response.data;
    } catch (e: any) {
      error.value = e.message;
    }
  }

  async function fetchHardware() {
    try {
      const response = await api.get('/api/v1/node/hardware');
      hardware.value = response.data;
    } catch (e: any) {
      error.value = e.message;
    }
  }

  async function fetchEvents(limit = 50) {
    try {
      const response = await api.get('/api/v1/node/events', { params: { limit } });
      events.value = response.data.events;
    } catch (e: any) {
      error.value = e.message;
    }
  }

  async function pauseNode() {
    try {
      await api.post('/api/v1/node/control/pause');
      await fetchHealth();
    } catch (e: any) {
      error.value = e.message;
    }
  }

  async function resumeNode() {
    try {
      await api.post('/api/v1/node/control/resume');
      await fetchHealth();
    } catch (e: any) {
      error.value = e.message;
    }
  }

  async function restartNode() {
    try {
      await api.post('/api/v1/node/control/restart');
    } catch (e: any) {
      error.value = e.message;
    }
  }

  function updateHardware(data: HardwareMetrics) {
    hardware.value = data;
  }

  function addEvent(event: NodeEvent) {
    events.value = [event, ...events.value.slice(0, 99)];
  }

  function updateTraining(data: any) {
    training.value = data;
  }

  return {
    info,
    health,
    hardware,
    events,
    training,
    loading,
    error,
    isOnline,
    isPaused,
    fetchInfo,
    fetchHealth,
    fetchHardware,
    fetchEvents,
    pauseNode,
    resumeNode,
    restartNode,
    updateHardware,
    addEvent,
    updateTraining,
  };
});
