<script setup>
import { ref } from 'vue'
import ImagesTab from './files/ImagesTab.vue'
import OpsPlansTab from './files/OpsPlansTab.vue'
import IntelSummariesTab from './files/IntelSummariesTab.vue'
import EODReportsTab from './files/EODReportsTab.vue'
import OtherTab from './files/OtherTab.vue'

const tabs = [
  { key: 'images', label: 'Images', icon: 'imagesmode' },
  { key: 'ops', label: 'Ops Plans', icon: 'map_pin_review' },
  { key: 'intel', label: 'Intel Summaries', icon: 'network_intelligence_update' },
  { key: 'eod', label: 'EOD Reports', icon: 'bedtime' },
  { key: 'other', label: 'Other', icon: 'picture_as_pdf' }
]
const active = ref('images')
</script>

<template>
  <div class="files">
    <div class="subtabs surface-card border-round p-1 mb-2">
      <div class="flex gap-1 wrap">
        <button
          v-for="t in tabs"
          :key="t.key"
          class="p-2 border-round flex align-items-center gap-2 cursor-pointer tab-btn"
          :class="{ active: t.key === active, inactive: t.key !== active }"
          @click="active = t.key"
        >
          <span class="material-symbols-outlined">{{ t.icon }}</span>
          <span class="label">{{ t.label }}</span>
        </button>
      </div>
    </div>

    <div>
      <ImagesTab v-if="active==='images'" />
      <OpsPlansTab v-else-if="active==='ops'" />
      <IntelSummariesTab v-else-if="active==='intel'" />
      <EODReportsTab v-else-if="active==='eod'" />
      <OtherTab v-else />
    </div>
  </div>
</template>

<style scoped>
.subtabs { position: sticky; top: 0; z-index: 1; }
.tab-btn { background: transparent; border: 1px solid transparent; }
.tab-btn:hover { background: var(--p-surface-100, #f5f5f5); }
.tab-btn.active { background: var(--p-primary-100, #fbd5d5); color: var(--p-primary-800, #1D3B52); border-color: var(--p-primary-200, #C9DFEE); }
.tab-btn.inactive { color: var(--p-text-color, inherit); }
.wrap { flex-wrap: wrap; }
</style>
