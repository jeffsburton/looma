<script setup>
const props = defineProps({
  caseId: { type: [String, Number], required: true }
})
</script>

<template>
  <div class="p-2">
    <div class="text-lg font-semibold mb-2">Tasks</div>
    <p class="text-600">This is a placeholder for Tasks related to this case (ID: {{ caseId }}).</p>
  </div>
</template>

<style scoped>
</style>
