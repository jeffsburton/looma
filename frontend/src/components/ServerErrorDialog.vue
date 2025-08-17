<script setup>
import { computed, ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import { serverErrorState, hideServerError } from '../lib/serverErrorStore'

const visible = computed({
  get: () => serverErrorState.visible,
  set: (val) => {
    if (!val) hideServerError()
  }
})

const showDetails = ref(false)

const hasDetails = computed(() => !!serverErrorState.details)

const prettyDetailsWithoutTrace = computed(() => {
  if (!serverErrorState.details) return ''
  const { trace, ...rest } = serverErrorState.details || {}
  try {
    // Remove empty fields for readability
    const pruned = Object.fromEntries(Object.entries(rest).filter(([_, v]) => v !== undefined && v !== null && v !== ''))
    return JSON.stringify(pruned, null, 2)
  } catch {
    return JSON.stringify(rest, null, 2)
  }
})

const traceLines = computed(() => {
  const t = serverErrorState.details?.trace
  if (!t) return []
  if (Array.isArray(t)) return t.flatMap((s) => String(s).split('\n'))
  return String(t).split('\n')
})

const copyAll = async () => {
  if (!serverErrorState.details) return
  const text = JSON.stringify(serverErrorState.details, null, 2)
  try {
    await navigator.clipboard.writeText(text)
  } catch (e) {
    console.error('Failed to copy error details', e)
  }
}
</script>

<template>
  <Dialog
    v-model:visible="visible"
    modal
    :closable="true"
    :draggable="false"
    header="Server Error"
    :style="{ width: '80vw', maxWidth: '1200px' }"
    :breakpoints="{ '1200px': '85vw', '960px': '90vw', '640px': '95vw' }"
  >
    <div class="flex flex-column gap-3">
      <div class="flex align-items-center gap-2">
        <i class="pi pi-exclamation-triangle" style="font-size:1.5rem;color:#dc2626" />
        <div class="font-medium">{{ serverErrorState.message || 'An unexpected server error occurred.' }}</div>
      </div>
      <div class="text-600" style="line-height:1.5">
        Something went wrong on our side. Please try again. If the problem persists, contact support and include the Error ID below.
      </div>

      <div v-if="serverErrorState.details?.error_id" class="flex align-items-center gap-2">
        <span class="text-700">Error ID:</span>
        <Tag :value="serverErrorState.details.error_id" severity="danger" />
      </div>

      <div class="flex gap-2">
        <Button size="small" :label="showDetails ? 'Hide Details' : 'Show Details'" icon="pi pi-chevron-down" :outlined="true" @click="showDetails = !showDetails"/>
        <Button v-if="showDetails && hasDetails" size="small" label="Copy Details" icon="pi pi-copy" @click="copyAll"/>
      </div>

      <div v-if="showDetails && hasDetails" class="surface-100 border-1 border-200 p-3 border-round overflow-auto details-panel">
        <template v-if="prettyDetailsWithoutTrace">
          <div class="mb-2 font-medium">Details</div>
          <pre class="m-0 json-block">{{ prettyDetailsWithoutTrace }}</pre>
        </template>
        <template v-if="traceLines.length">
          <div class="mt-3 mb-2 font-medium">Stack Trace</div>
          <pre class="m-0 trace-block">
<span v-for="(line, idx) in traceLines" :key="idx">{{ line }}
</span>
          </pre>
        </template>
      </div>

      <div class="flex justify-content-end gap-2 mt-2">
        <Button label="Close" @click="hideServerError" />
      </div>
    </div>
  </Dialog>
</template>

<style scoped>
.details-panel { max-height: 70vh; }
.json-block { white-space: pre-wrap; word-wrap: break-word; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.9rem; }
.trace-block { white-space: pre; overflow: auto; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.9rem; line-height: 1.35; }
</style>
