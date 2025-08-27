<script setup>
import { ref } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import SidebarMenu from '../components/SidebarMenu.vue'
import HospitalsTab from '../components/admin/HospitalsTab.vue'
import RfiSourcesTab from '../components/admin/RfiSourcesTab.vue'

const activeTab = ref('Organizations')
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Admin'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Admin</div>
          </div>

          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <Tabs :value="activeTab" @update:value="(v) => (activeTab = v)">
              <TabList class="mb-2">
                <Tab value="Hospitals">ER's/Trauma Centers</Tab>
                <Tab value="RfiSources">RFI Sources</Tab>
              </TabList>
              <TabPanels>
                <TabPanel value="Hospitals">
                  <div class="p-2 text-700">
                    <HospitalsTab />
                  </div>
                </TabPanel>
                <TabPanel value="RfiSources">
                  <div class="p-2 text-700">
                    <RfiSourcesTab />
                  </div>
                </TabPanel>
              </TabPanels>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Using PrimeVue Tabs components; custom tabbar styles removed */
</style>
