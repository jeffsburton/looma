<script setup>
import { ref, watch, computed } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import IntakeTab from './core/IntakeTab.vue'
import StatusTab from './core/StatusTab.vue'
import ContactsTab from './core/ContactsTab.vue'
import VictimologyTab from './core/VictimologyTab.vue'
import SearchUrgencyTab from './core/SearchUrgencyTab.vue'
import SocialMediaTab from './core/SocialMediaTab.vue'

const props = defineProps({
  subtab: { type: String, default: 'intake' },
  caseModel: { type: Object, default: () => ({}) },
  subjectModel: { type: Object, default: () => ({}) },
  demographicsModel: { type: Object, default: () => ({}) },
  managementModel: { type: Object, default: () => ({}) },
  patternOfLifeModel: { type: Object, default: () => ({}) },
  dispositionModel: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['update:subtab','update:caseModel','update:subjectModel','update:demographicsModel','update:managementModel','update:patternOfLifeModel','update:dispositionModel'])

const VALID_SUBTABS = ['intake','status','contacts','victimology','social','urgency']

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
    <Tabs :value="active" @update:value="(v) => (active = v)">
      <TabList class="mb-2">
        <Tab value="intake">
          <span class="material-symbols-outlined">arrows_input</span>
          <span class="ml-1">Intake</span>
        </Tab>
        <Tab value="status">
          <span class="material-symbols-outlined">check</span>
          <span class="ml-1">Status</span>
        </Tab>
        <Tab value="contacts">
          <span class="material-symbols-outlined">patient_list</span>
          <span class="ml-1">People</span>
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
        <TabPanel value="intake">
          <IntakeTab
            :caseModel="props.caseModel"
            :subjectModel="props.subjectModel"
            :demographicsModel="props.demographicsModel"
            :managementModel="props.managementModel"
            :patternOfLifeModel="props.patternOfLifeModel"
            @update:caseModel="(v) => emit('update:caseModel', v)"
            @update:subjectModel="(v) => emit('update:subjectModel', v)"
            @update:demographicsModel="(v) => emit('update:demographicsModel', v)"
            @update:managementModel="(v) => emit('update:managementModel', v)"
            @update:patternOfLifeModel="(v) => emit('update:patternOfLifeModel', v)"
          />
        </TabPanel>
        <TabPanel value="status">
          <StatusTab
            :caseModel="props.caseModel"
            :dispositionModel="props.dispositionModel"
            @update:caseModel="(v) => emit('update:caseModel', v)"
            @update:dispositionModel="(v) => emit('update:dispositionModel', v)"
          />
        </TabPanel>
        <TabPanel value="contacts">
          <ContactsTab :caseId="props.caseModel.id" />
        </TabPanel>
        <TabPanel value="victimology">
          <template v-if="props.caseModel && props.caseModel.id">
            <VictimologyTab :caseId="props.caseModel.id" />
          </template>
          <template v-else>
            <div class="p-3 text-500">Loading case...</div>
          </template>
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
