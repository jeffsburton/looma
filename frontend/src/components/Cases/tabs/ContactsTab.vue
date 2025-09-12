<script setup>
import { ref, watch, computed, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

// Async child tabs
const SubjectsTab = defineAsyncComponent(() => import('./SubjectsTab.vue'))
const PersonsTab = defineAsyncComponent(() => import('./PersonsTab.vue'))

const props = defineProps({
  caseId: { type: [String, Number], default: '' },
})

const route = useRoute()
const router = useRouter()

const active = ref('subjects')

// Sync active sub-tab with route or deep-link params
watch(
  () => ({ subtab: route.params.subtab, rawSubjectId: route.params.rawSubjectId, rawPersonId: route.params.rawPersonId }),
  (val) => {
    // Determine desired subtab
    let desired = String(val?.subtab || '')
    if (!desired) {
      if (val?.rawSubjectId) desired = 'subjects'
      else if (val?.rawPersonId) desired = 'persons'
      else desired = 'subjects'
    }
    if (active.value !== desired) active.value = desired
  },
  { immediate: true, deep: true }
)

watch(
  () => active.value,
  (v) => {
    // While editing a contact via deep-link, do not rewrite the URL/subtab
    if (route.params.rawSubjectId || route.params.rawPersonId) return
    const caseNumber = String(route.params.caseNumber || '')
    const sub = String(v || 'subjects')
    if (String(route.params.subtab || '') !== sub) {
      router.replace({ name: 'case-detail', params: { caseNumber, tab: 'contacts', subtab: sub } })
    }
  }
)
</script>

<template>
  <div class="">
    <Tabs :value="active" @update:value="(v) => (active = v)" :lazy="true">
      <TabList class="mb-1">
        <Tab value="subjects">
          <span class="material-symbols-outlined">group</span>
          <span class="ml-1">Investigatory Subjects</span>
        </Tab>
        <Tab value="persons">
          <span class="material-symbols-outlined">badge</span>
          <span class="ml-1">Agency Personnel</span>
        </Tab>
      </TabList>
      <TabPanels>
        <TabPanel value="subjects">
          <Suspense>
            <SubjectsTab :caseId="String(caseId)" />
            <template #fallback>
              <div class="p-3 text-600">Loading...</div>
            </template>
          </Suspense>
        </TabPanel>
        <TabPanel value="persons">
          <Suspense>
            <PersonsTab :caseId="String(caseId)" />
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
</style>
