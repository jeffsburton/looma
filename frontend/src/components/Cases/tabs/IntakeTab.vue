<script setup>
import { ref } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import CoreTab from './intake/CoreTab.vue'
import StatusTab from './intake/StatusTab.vue'
import ContactsTab from './intake/ContactsTab.vue'
import VictomologyTab from './intake/VictomologyTab.vue'
import SearchUrgencyTab from './intake/SearchUrgencyTab.vue'
import SocialMediaTab from './intake/SocialMediaTab.vue'

const active = ref('core')
</script>

<template>
  <div class="intake">
    <Tabs :value="active" @update:value="(v) => (active = v)">
      <TabList class="mb-2">
        <Tab value="core">
          <span class="material-symbols-outlined">arrows_input</span>
          <span class="ml-1">Intake</span>
        </Tab>
        <Tab value="status">
          <span class="material-symbols-outlined">check</span>
          <span class="ml-1">Status</span>
        </Tab>
        <Tab value="contacts">
          <span class="material-symbols-outlined">patient_list</span>
          <span class="ml-1">Contacts</span>
        </Tab>
        <Tab value="victomology">
          <span class="material-symbols-outlined">heart_broken</span>
          <span class="ml-1">Victomology</span>
        </Tab>
        <Tab value="social">
          <span class="material-symbols-outlined">share</span>
          <span class="ml-1">Social Media</span>
        </Tab>
        <Tab value="urgency">
          <span class="material-symbols-outlined">zone_person_urgent</span>
          <span class="ml-1">Search Urgency</span>
        </Tab>
      </TabList>

      <TabPanels>
        <TabPanel value="core">
          <CoreTab />
        </TabPanel>
        <TabPanel value="status">
          <StatusTab />
        </TabPanel>
        <TabPanel value="contacts">
          <ContactsTab />
        </TabPanel>
        <TabPanel value="victomology">
          <VictomologyTab />
        </TabPanel>
        <TabPanel value="social">
          <SocialMediaTab />
        </TabPanel>
        <TabPanel value="urgency">
          <SearchUrgencyTab />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
/* Using PrimeVue Tabs components for subtabs */
</style>
