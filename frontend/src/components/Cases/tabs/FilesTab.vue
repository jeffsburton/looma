<script setup>
import { ref, watch } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import ImagesTab from './files/ImagesTab.vue'
import OpsPlansTab from './files/OpsPlansTab.vue'
import IntelSummariesTab from './files/IntelSummariesTab.vue'
import RFIsTab from './files/RFIsTab.vue'
import EODReportsTab from './files/EODReportsTab.vue'
import MissingFlyerTab from './files/MissingFlyerTab.vue'
import OtherTab from './files/OtherTab.vue'

const props = defineProps({
  caseId: { type: [String, Number], required: false },
  subtab: { type: String, default: 'images' }
})
const emit = defineEmits(['update:subtab'])

const VALID_SUBTABS = ['images','ops','intel','rfis','eod','flyer','other']

const active = ref('images')

// Initialize and sync from prop
watch(
  () => props.subtab,
  (val) => {
    let v = String(val || 'images')
    if (!VALID_SUBTABS.includes(v)) v = 'images'
    if (active.value !== v) active.value = v
  },
  { immediate: true }
)

// Emit up when local changes
watch(
  () => active.value,
  (v) => {
    const sub = String(v || 'images')
    if (!VALID_SUBTABS.includes(sub)) return
    emit('update:subtab', sub)
  }
)
</script>

<template>
  <div class="files">
    <Tabs v-model:value="active">
      <TabList class="mb-2">
        <Tab value="images">
          <span class="material-symbols-outlined">imagesmode</span>
          <span class="ml-1">Images</span>
        </Tab>
        <Tab value="other">
          <span class="material-symbols-outlined">picture_as_pdf</span>
          <span class="ml-1">Other</span>
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
        <TabPanel value="images">
          <ImagesTab :caseId="caseId" />
        </TabPanel>
        <TabPanel value="ops">
          <OpsPlansTab />
        </TabPanel>
        <TabPanel value="intel">
          <IntelSummariesTab />
        </TabPanel>
        <TabPanel value="rfis">
          <RFIsTab />
        </TabPanel>
        <TabPanel value="eod">
          <EODReportsTab />
        </TabPanel>
        <TabPanel value="flyer">
          <MissingFlyerTab />
        </TabPanel>
        <TabPanel value="other">
          <OtherTab :caseId="caseId" />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
/* Using PrimeVue Tabs components for subtabs */
</style>
