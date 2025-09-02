<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useToast } from 'primevue/usetoast'
import SidebarMenu from '../components/SidebarMenu.vue'
import SelectButton from 'primevue/selectbutton'
import Button from 'primevue/button'
import { getCookie, setCookie } from '../lib/cookies'
import { hasPermission } from '../lib/permissions'

import CaseProfilesLarge from '../components/cases/CaseProfilesLarge.vue'
import CaseProfilesSmall from '../components/cases/CaseProfilesSmall.vue'
import CaseProfilesList from '../components/cases/CaseProfilesList.vue'

const toast = useToast()

const COOKIE_KEY = 'ui_cases_view'
const VALID_VIEWS = ['large','small','list']
const view = ref('large')
const viewOptions = [
  { label: 'crop_landscape', value: 'large' },
  { label: 'view_cozy', value: 'small' },
  { label: 'table_rows', value: 'list' }
]

const cases = ref([])
const loading = ref(false)

const canModify = computed(() => hasPermission('CASES.MODIFY'))

async function loadCases() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/cases/select', { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (resp.status === 401) {
      toast.add({ severity: 'warn', summary: 'Authentication required', detail: 'Please sign in to view cases.', life: 3500 })
      cases.value = []
      return
    }
    if (!resp.ok) throw new Error('Failed to load cases')
    const items = await resp.json()
    // Map API fields to component-friendly fields
    cases.value = (items || []).map(it => ({
      id: it.id,
      rawId: it.raw_db_id,
      name: it.name,
      photoUrl: it.photo_url,
      caseNumber: it.id,
      // age/missingDays/contacts unknown from API; leave undefined
    }))
  } catch (err) {
    // Provide a user-friendly message and avoid unhandled promise rejections
    const message = err instanceof Error ? err.message : 'Unexpected error'
    toast.add({ severity: 'error', summary: 'Failed to load cases', detail: message, life: 3500 })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Restore view from cookie if present and valid
  try {
    const saved = getCookie(COOKIE_KEY)
    if (saved && VALID_VIEWS.includes(saved)) {
      view.value = saved
    }
  } catch (_) { /* noop */ }
  loadCases()
})

// Persist view changes (mirror Sidebar cookie logic: 1 year, Lax)
watch(view, (v) => {
  try {
    if (VALID_VIEWS.includes(v)) {
      setCookie(COOKIE_KEY, v, { maxAge: 60 * 60 * 24 * 365, sameSite: 'Lax' })
    }
  } catch (_) { /* noop */ }
})
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
          <!-- Toolbar with SelectButton and Add button -->
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Cases</div>
            <div class="flex align-items-center gap-2">
              <Button v-if="canModify" label="Add" icon="pi pi-plus" @click="() => toast.add({ severity: 'info', summary: 'Coming soon', detail: 'New Case creation is not implemented yet.', life: 2500 })" />
              <SelectButton v-model="view" :options="viewOptions" optionValue="value" optionLabel="label">
                <template #option="{ option }">
                  <span class="material-symbols-outlined">{{ option.label }}</span>
                </template>
              </SelectButton>
            </div>
          </div>

          <!-- Content panel -->
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <CaseProfilesLarge v-if="view === 'large'" :cases="cases" />
            <CaseProfilesSmall v-else-if="view === 'small'" :cases="cases" />
            <CaseProfilesList v-else :cases="cases" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
