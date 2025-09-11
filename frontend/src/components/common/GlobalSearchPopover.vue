<script setup>
import { ref, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import Popover from 'primevue/popover'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'
import api from '../../lib/api'

// Public API: parent can call open(event)
const pop = ref()
const inputEl = ref()
const router = useRouter()

const q = ref('')
const hits = ref([])
const loading = ref(false)
const error = ref('')
let t = null

function resetState() {
  q.value = ''
  hits.value = []
  loading.value = false
  error.value = ''
}

function open(event) {
  // Toggle popover at the click event position and prepare the UI
  if (pop.value) {
    pop.value.toggle(event)
    // Small delay to ensure popover is in DOM
    nextTick(() => {
      try { inputEl.value?.focus() } catch {}
    })
  }
  resetState()
}

async function runSearch(term) {
  if (!term || term.length < 2) {
    hits.value = []
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/api/v1/search', { params: { q: term } })
    const list = Array.isArray(data?.hits) ? data.hits : []
    // Normalize paths (support either primary_path or path)
    hits.value = list.filter(h => typeof h?.primary_path === 'string' || typeof h?.path === 'string')
  } catch (e) {
    // Fail quietly in UI
    error.value = 'Search unavailable'
    hits.value = []
  } finally {
    loading.value = false
  }
}

function onInput() {
  if (t) clearTimeout(t)
  t = setTimeout(() => runSearch(q.value.trim()), 300)
}

function go(hit) {
  const path = hit?.primary_path || hit?.path
  if (!path) return
  router.push(path)
  // Close popover after navigation
  try { pop.value?.hide() } catch {}
}

// Expose open to parent
defineExpose({ open })
</script>

<template>
  <Popover ref="pop" :dismissable="true" class="global-search-pop">
    <div class="w-20rem">
      <FloatLabel variant="on" class="w-full">
        <InputText
          id="globalSearch"
          ref="inputEl"
          v-model="q"
          class="w-full"
          placeholder="Type to search..."
          @input="onInput"
        />
        <label for="globalSearch">Search</label>
      </FloatLabel>

      <div class="mt-2" v-if="loading">
        <span class="text-500 text-sm">Searching…</span>
      </div>
      <div class="mt-2 text-sm text-500" v-else-if="!q || q.length < 2">
        Type at least 2 characters
      </div>
      <div class="mt-2 text-sm text-500" v-else-if="error">
        {{ error }}
      </div>
      <ul v-else class="results list-none m-0 p-0">
        <li v-for="(h, i) in hits" :key="i" class="res-item" @mousedown.prevent="go(h)">
          <div class="title text-900">{{ h.title || h.entity_type || 'Result' }}</div>
          <div class="sub text-600 text-sm" v-if="h.subtitle">{{ h.subtitle }}</div>
        </li>
        <li v-if="!hits.length" class="text-600 text-sm">No results</li>
      </ul>
    </div>
  </Popover>
</template>

<style scoped>
.global-search-pop :deep(.p-popover-content) {
  padding: .75rem;
}
.res-item {
  padding: .35rem .25rem;
  border-radius: .375rem;
  cursor: pointer;
}
.res-item:hover { background: var(--p-surface-100, #f5f5f5); }
.title { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sub { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
