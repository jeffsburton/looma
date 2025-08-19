<script setup>
import { ref } from 'vue'
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

const active = ref('images')
</script>

<template>
  <div class="files">
    <Tabs :value="active" @update:value="(v) => (active = v)">
      <TabList class="mb-2">
        <Tab value="images">
          <span class="material-symbols-outlined">imagesmode</span>
          <span class="ml-1">Images</span>
        </Tab>
        <Tab value="ops">
          <span class="material-symbols-outlined">map_pin_review</span>
          <span class="ml-1">Ops Plans</span>
        </Tab>
        <Tab value="intel">
          <span class="material-symbols-outlined">network_intelligence_update</span>
          <span class="ml-1">Intel Summaries</span>
        </Tab>
        <Tab value="rfi">
          <span class="material-symbols-outlined">quiz</span>
          <span class="ml-1">RFI's</span>
        </Tab>
        <Tab value="eod">
          <span class="material-symbols-outlined">bedtime</span>
          <span class="ml-1">EOD Reports</span>
        </Tab>
        <Tab value="missing">
          <span class="material-symbols-outlined">contact_phone</span>
          <span class="ml-1">Missing Flyer</span>
        </Tab>
        <Tab value="other">
          <span class="material-symbols-outlined">picture_as_pdf</span>
          <span class="ml-1">Other</span>
        </Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="images">
          <ImagesTab />
        </TabPanel>
        <TabPanel value="ops">
          <OpsPlansTab />
        </TabPanel>
        <TabPanel value="intel">
          <IntelSummariesTab />
        </TabPanel>
        <TabPanel value="rfi">
          <RFIsTab />
        </TabPanel>
        <TabPanel value="eod">
          <EODReportsTab />
        </TabPanel>
        <TabPanel value="missing">
          <MissingFlyerTab />
        </TabPanel>
        <TabPanel value="other">
          <OtherTab />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
/* Using PrimeVue Tabs components for subtabs */
</style>
