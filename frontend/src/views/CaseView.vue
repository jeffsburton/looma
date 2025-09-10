<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SidebarMenu from '../components/SidebarMenu.vue'
import CaseEdit from '../components/cases/CaseEdit.vue'

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const tab = computed(() => route.name === 'case-task' ? 'tasks' : String(route.params.tab || 'core'))
const subtab = computed(() => String(route.params.subtab || 'intake'))

function goBackToList() {
  router.replace({ name: 'cases' })
}
</script>

<template>

  <div class="h-screen flex surface-50">
    <!-- Left Panel -->
    <div class="flex-shrink-0 overflow-hidden p-2">
      <SidebarMenu :active="'Cases'" />
    </div>

    <!-- Right Side Container -->
    <div class="flex-1 flex flex-col min-w-0 p-2" style="flex-direction: column;">
      <!-- Top Right Panel -->
      <div class="flex-shrink-0 bg-blue-100 border-b">
          <div class="surface-card border-round p-2 flex-1 ">
            <!-- Header with back arrow -->
            <div class="flex align-items-center gap-2 mb-2">
              <button class="icon-button" @click="goBackToList" title="Back">
                <span class="material-symbols-outlined">arrow_back</span>
              </button>
              <div class="text-lg font-semibold">Case {{ caseNumber }}</div>
            </div>
          </div>
      </div>

      <!-- Bottom Right Panel (Scrollable) -->
      <div class="flex-1 overflow-auto ">

            <CaseEdit :caseNumber="caseNumber" :tab="tab" :subtab="subtab" />
      </div>
    </div>
  </div>


</template>

<style scoped>
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
</style>
