import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { useNodeStore } from './nodeStore';
import { useMetricsStore } from './metricsStore';

export const useWebSocketStore = defineStore('websocket', () => {
  const connected = ref(false);
  const connectionId = ref<string | null>(null);
  const subscriptions = ref<string[]>([]);
  const reconnecting = ref(false);

  let ws: WebSocket | null = null;
  let reconnectTimeout: number | null = null;

  const isConnected = computed(() => connected.value);

  async function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/v1/node`;

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        connected.value = true;
        reconnecting.value = false;
        connectionId.value = `ws_${Date.now()}`;

        // Subscribe to channels
        subscribe(['stats', 'hardware', 'events', 'training']);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onclose = () => {
        connected.value = false;
        scheduleReconnect();
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      scheduleReconnect();
    }
  }

  function disconnect() {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout);
      reconnectTimeout = null;
    }

    if (ws) {
      ws.close();
      ws = null;
    }

    connected.value = false;
  }

  function subscribe(channels: string[]) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'subscribe',
        channels,
      }));
      subscriptions.value = [...new Set([...subscriptions.value, ...channels])];
    }
  }

  function unsubscribe(channels: string[]) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'unsubscribe',
        channels,
      }));
      subscriptions.value = subscriptions.value.filter(c => !channels.includes(c));
    }
  }

  function handleMessage(message: any) {
    const nodeStore = useNodeStore();
    const metricsStore = useMetricsStore();

    switch (message.type) {
      case 'stats':
        metricsStore.updateFromWebSocket(message.data);
        break;
      case 'hardware':
        nodeStore.updateHardware(message.data);
        break;
      case 'events':
        nodeStore.addEvent(message.data);
        break;
      case 'training':
        nodeStore.updateTraining(message.data);
        break;
      case 'subscribed':
      case 'unsubscribed':
        // Subscription confirmation
        break;
      default:
        console.log('Unknown message type:', message.type);
    }
  }

  function scheduleReconnect() {
    if (!reconnecting.value) {
      reconnecting.value = true;
      reconnectTimeout = window.setTimeout(() => {
        connect();
      }, 5000);
    }
  }

  return {
    connected,
    connectionId,
    subscriptions,
    reconnecting,
    isConnected,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
  };
});
