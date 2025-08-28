<script setup>
import { ref, computed, watchEffect, defineAsyncComponent } from 'vue'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import SidebarMenu from '../components/SidebarMenu.vue'
import { hasPermission } from '../lib/permissions'

// Define all possible admin tabs with their permission and lazy component
const allTabs = [
  {
    value: 'Hospitals',
    label: "ER's/Trauma Centers",
    perm: 'HOSPITAL_ER',
    component: defineAsyncComponent(() => import('../components/admin/HospitalsTab.vue'))
  },
  {
    value: 'RfiSources',
    label: 'RFI Sources',
    perm: 'RFI_SOURCES',
    component: defineAsyncComponent(() => import('../components/admin/RfiSourcesTab.vue'))
  },
  {
    value: 'Organizations',
    label: 'Organizations',
    perm: 'ORGS',
    component: defineAsyncComponent(() => import('../components/admin/OrganizationsTab.vue'))
  },
  {
    value: 'Qualifications',
    label: 'Qualifications',
    perm: 'QUALIFICATIONS',
    component: defineAsyncComponent(() => import('../components/admin/QualificationsTab.vue'))
  }
]

// Filter by permissions
const visibleTabs = computed(() => allTabs.filter(t => hasPermission(t.perm)))

// Active tab is the first visible by default
const activeTab = ref('')
watchEffect(() => {
  const first = visibleTabs.value[0]
  if (!first) {
    activeTab.value = ''
    return
  }
  // If current active is not in visible list, or empty, set to first
  const stillVisible = visibleTabs.value.some(t => t.value === activeTab.value)
  if (!stillVisible) activeTab.value = first.value
})
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
            <div v-if="!visibleTabs.length" class="p-3 text-700">
              You do not have access to any admin tabs.
            </div>
            <Tabs v-else :value="activeTab" @update:value="(v) => (activeTab = v)">
              <TabList class="mb-2">
                <Tab v-for="t in visibleTabs" :key="t.value" :value="t.value">{{ t.label }}</Tab>
              </TabList>
              <TabPanels>
                <TabPanel v-for="t in visibleTabs" :key="t.value" :value="t.value">
                  <div class="p-2 text-700">
                    <!-- Lazy load component; only render when active to avoid mounting others -->
                    <component v-if="activeTab === t.value" :is="t.component" />
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
