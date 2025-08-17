<script setup>
import { ref } from 'vue'
import CoreTab from './intake/CoreTab.vue'
import StatusTab from './intake/StatusTab.vue'
import ContactsTab from './intake/ContactsTab.vue'
import VictomologyTab from './intake/VictomologyTab.vue'
import SearchUrgencyTab from './intake/SearchUrgencyTab.vue'
import SocialMediaTab from './intake/SocialMediaTab.vue'

const tabs = [
  { key: 'core', label: 'Intake', icon: 'arrows_input' },
  { key: 'status', label: 'Status', icon: 'check' },
  { key: 'contacts', label: 'Contacts', icon: 'patient_list' },
  { key: 'victomology', label: 'Victomology', icon: 'heart_broken' },
  { key: 'social', label: 'Social Media', icon: 'share' },
  { key: 'urgency', label: 'Search Urgency', icon: 'zone_person_urgent' }
]
const active = ref('core')
</script>

<template>
  <div class="intake">
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
      <CoreTab v-if="active==='core'" />
      <StatusTab v-else-if="active==='status'" />
      <ContactsTab v-else-if="active==='contacts'" />
      <VictomologyTab v-else-if="active==='victomology'" />
      <SocialMediaTab v-else-if="active==='social'" />
      <SearchUrgencyTab v-else />
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
