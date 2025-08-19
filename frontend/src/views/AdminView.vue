<script setup>
import { ref } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import SidebarMenu from '../components/SidebarMenu.vue'
import OrganizationsTab from '../components/admin/OrganizationsTab.vue'
import TeamsTab from '../components/admin/TeamsTab.vue'
import QualificationsTab from '../components/admin/QualificationsTab.vue'

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
                <Tab value="Organizations">Organizations</Tab>
                <Tab value="Teams">Teams</Tab>
                <Tab value="Qualifications">Qualifications</Tab>
              </TabList>
              <TabPanels>
                <TabPanel value="Organizations">
                  <div class="p-2 text-700">
                    <OrganizationsTab />
                  </div>
                </TabPanel>
                <TabPanel value="Teams">
                  <div class="p-2 text-700">
                    <TeamsTab />
                  </div>
                </TabPanel>
                <TabPanel value="Qualifications">
                  <div class="p-2 text-700">
                    <QualificationsTab />
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
