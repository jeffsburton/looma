<script setup>
import { ref, watch, defineAsyncComponent } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import FilesTab from './docs/FilesTab.vue'
import OpsPlansTab from './docs/OpsPlansTab.vue'
import IntelSummariesTab from './docs/IntelSummariesTab.vue'
import RFIsTab from './docs/RFIsTab.vue'
import EODReportsTab from './docs/EODReportsTab.vue'
import MissingFlyerTab from './docs/MissingFlyerTab.vue'

const props = defineProps({
  caseId: { type: [String, Number], required: true },
  subtab: { type: String, default: 'files' }
})
const emit = defineEmits(['update:subtab'])

const VALID_SUBTABS = ['files','ops','intel','rfis','eod','flyer']

const active = ref('files')

// Initialize and sync from prop
watch(
  () => props.subtab,
  (val) => {
    let v = String(val || 'files')
    if (!VALID_SUBTABS.includes(v)) v = 'files'
    if (active.value !== v) active.value = v
  },
  { immediate: true }
)

// Emit up when local changes
watch(
  () => active.value,
  (v) => {
    const sub = String(v || 'files')
    if (!VALID_SUBTABS.includes(sub)) return
    emit('update:subtab', sub)
  }
)
</script>

<template>
  <div class="files">
    <Tabs v-model:value="active" :lazy="true">
      <TabList class="mb-2">
        <Tab value="files">
          <span class="material-symbols-outlined">picture_as_pdf</span>
          <span class="ml-1">Files</span>
        </Tab>
        <Tab value="ops">
          <span class="material-symbols-outlined">map_pin_review</span>
          <span class="ml-1">Ops Plans</span>
        </Tab>
        <Tab value="intel">
          <span class="material-symbols-outlined">network_intelligence_update</span>
          <span class="ml-1">Intel Summaries</span>
        </Tab>
        <Tab value="rfis">
          <span class="material-symbols-outlined">quiz</span>
          <span class="ml-1">RFI's</span>
        </Tab>
        <Tab value="eod">
          <span class="material-symbols-outlined">bedtime</span>
          <span class="ml-1">EOD Reports</span>
        </Tab>
        <Tab value="flyer">
          <span class="material-symbols-outlined">contact_phone</span>
          <span class="ml-1">Missing Flyer</span>
        </Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="files">
          <Suspense>
            <FilesTab :caseId="caseId" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="ops">
          <Suspense>
            <OpsPlansTab />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="intel">
          <Suspense>
            <IntelSummariesTab />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="rfis">
          <Suspense>
            <RFIsTab />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="eod">
          <Suspense>
            <EODReportsTab />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="flyer">
          <Suspense>
            <MissingFlyerTab />
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
