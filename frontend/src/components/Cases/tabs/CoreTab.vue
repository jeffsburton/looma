<script setup>
import { ref, watch, defineAsyncComponent } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

// Lazy imports for core subtabs
const IntakeTab = defineAsyncComponent(() => import('./core/IntakeTab.vue'))
const StatusTab = defineAsyncComponent(() => import('./core/StatusTab.vue'))
const VictimologyTab = defineAsyncComponent(() => import('./core/VictimologyTab.vue'))
const SearchUrgencyTab = defineAsyncComponent(() => import('./core/SearchUrgencyTab.vue'))
const CircumstancesTab = defineAsyncComponent(() => import('./core/CircumstancesTab.vue'))

const props = defineProps({
  subtab: { type: String, default: 'intake' },
  caseId: { type: [String, Number], default: '' },
})
const emit = defineEmits(['update:subtab'])

const VALID_SUBTABS = ['intake','status','victimology','circumstances','urgency']

const active = ref('intake')

// Initialize and sync from prop
watch(
  () => props.subtab,
  (val) => {
    let v = String(val || 'intake')
    if (!VALID_SUBTABS.includes(v)) v = 'intake'
    if (active.value !== v) active.value = v
  },
  { immediate: true }
)

// Emit up when local changes
watch(
  () => active.value,
  (v) => {
    const sub = String(v || 'status')
    if (!VALID_SUBTABS.includes(sub)) return
    // Avoid redundant emit if nothing changed
    if (sub === String(props.subtab || 'intake')) return
    emit('update:subtab', sub)
  }
)
</script>

<template>
  <div class="intake">
    <Tabs :value="active" @update:value="(v) => (active = v)" :lazy="true">
      <TabList class="mb-2">
        <Tab value="intake">
          <span class="material-symbols-outlined">arrows_input</span>
          <span class="ml-1">Intake</span>
        </Tab>
        <Tab value="status">
          <span class="material-symbols-outlined">check</span>
          <span class="ml-1">Status</span>
        </Tab>
        <Tab value="victimology">
          <span class="material-symbols-outlined">heart_broken</span>
          <span class="ml-1">Victimology</span>
        </Tab>
        <Tab value="circumstances">
          <span class="material-symbols-outlined">info</span>
          <span class="ml-1">Circumstances</span>
        </Tab>
        <Tab value="urgency">
          <span class="material-symbols-outlined">zone_person_urgent</span>
          <span class="ml-1">Search Urgency</span>
        </Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="intake">
          <Suspense>
            <IntakeTab :caseId="props.caseId" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="status">
          <Suspense>
            <StatusTab :caseId="props.caseId" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="victimology">
          <template v-if="props.caseId">
            <Suspense>
              <VictimologyTab :caseId="props.caseId" />
              <template #fallback>
                <div class="p-3 text-600">Loading...</div>
              </template>
            </Suspense>
          </template>
          <template v-else>
            <div class="p-3 text-500">Loading case...</div>
          </template>
        </TabPanel>
        <TabPanel value="circumstances">
          <Suspense>
            <CircumstancesTab :caseId="props.caseId || ''" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="urgency">
          <Suspense>
            <SearchUrgencyTab :caseId="props.caseId || ''" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
/* Using PrimeVue Tabs components for subtabs */
</style>
