<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SidebarMenu from '../components/SidebarMenu.vue'
import CaseEdit from '../components/cases/CaseEdit.vue'

const route = useRoute()
const router = useRouter()

const caseNumber = computed(() => String(route.params.caseNumber || ''))
const tab = computed(() => String(route.params.tab || 'core'))
const subtab = computed(() => String(route.params.subtab || 'intake'))

function goBackToList() {
  router.replace({ name: 'cases' })
}
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Cases'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <!-- Header with back arrow -->
            <div class="flex align-items-center gap-2 mb-2">
              <button class="icon-button" @click="goBackToList" title="Back">
                <span class="material-symbols-outlined">arrow_back</span>
              </button>
              <div class="text-lg font-semibold">Case {{ caseNumber }}</div>
            </div>
            <CaseEdit :caseNumber="caseNumber" :tab="tab" :subtab="subtab" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
</style>
