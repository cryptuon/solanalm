import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

export const useSettingsStore = defineStore('settings', () => {
  const darkMode = ref(true);
  const refreshInterval = ref(5000);
  const notificationsEnabled = ref(true);
  const compactView = ref(false);

  function toggleDarkMode() {
    darkMode.value = !darkMode.value;
    if (darkMode.value) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    saveSettings();
  }

  function loadSettings() {
    const saved = localStorage.getItem('solanalm-settings');
    if (saved) {
      const settings = JSON.parse(saved);
      darkMode.value = settings.darkMode ?? true;
      refreshInterval.value = settings.refreshInterval ?? 5000;
      notificationsEnabled.value = settings.notificationsEnabled ?? true;
      compactView.value = settings.compactView ?? false;
    }
  }

  function saveSettings() {
    localStorage.setItem('solanalm-settings', JSON.stringify({
      darkMode: darkMode.value,
      refreshInterval: refreshInterval.value,
      notificationsEnabled: notificationsEnabled.value,
      compactView: compactView.value,
    }));
  }

  return {
    darkMode,
    refreshInterval,
    notificationsEnabled,
    compactView,
    toggleDarkMode,
    loadSettings,
    saveSettings,
  };
});
