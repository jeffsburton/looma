<script setup>
import { ref, watch, computed } from 'vue'
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

const props = defineProps({
  subtab: { type: String, default: 'status' }
})
const emit = defineEmits(['update:subtab'])

const VALID_SUBTABS = ['core','status','contacts','victimology','social','urgency']

const active = ref('status')

// Initialize and sync from prop
watch(
  () => props.subtab,
  (val) => {
    let v = String(val || 'status')
    if (!VALID_SUBTABS.includes(v)) v = 'status'
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
    emit('update:subtab', sub)
  }
)
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
        <Tab value="victimology">
          <span class="material-symbols-outlined">heart_broken</span>
          <span class="ml-1">victimology</span>
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
        <TabPanel value="victimology">
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
