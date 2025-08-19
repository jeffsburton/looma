<script setup>
import ServerErrorDialog from './components/ServerErrorDialog.vue'
import Toast from 'primevue/toast'
</script>

<template>
  <router-view />
  <ServerErrorDialog />
  <Toast />
</template>
