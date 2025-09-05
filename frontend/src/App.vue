<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useToast } from 'primevue/usetoast'
import ServerErrorDialog from './components/ServerErrorDialog.vue'
import Toast from 'primevue/toast'

const toast = useToast()

function handleAppToast(e) {
  const payload = e?.detail
  if (payload) toast.add(payload)
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    window.addEventListener('app:toast', handleAppToast)
  }
})

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('app:toast', handleAppToast)
  }
})
</script>

<template>
  <router-view />
  <ServerErrorDialog />
  <Toast />
</template>
