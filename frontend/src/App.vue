<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import ServerErrorDialog from './components/ServerErrorDialog.vue'
import Toast from 'primevue/toast'
import { useSessionRefresher } from '@/composables/useSessionRefresher'

const toast = useToast()
const refresher = useSessionRefresher({
  // You can tune thresholds here if needed
  // intervalMs: 60_000,
  // activeWindowMs: 5 * 60_000,
  // minBetweenRefreshMs: 5 * 60_000,
  // refreshWhenExpInMin: 10,
})

function handleAppToast(e) {
  const payload = e?.detail
  if (payload) toast.add(payload)
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('app:toast', handleAppToast)
  }
  refresher.start()
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('app:toast', handleAppToast)
  }
  refresher.stop()
})
</script>

<template>
  <router-view />
  <ServerErrorDialog />
  <Toast />
</template>
