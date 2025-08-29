<script setup>
import { ref, computed, onMounted } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import SelectButton from 'primevue/selectbutton'
import InputSwitch from 'primevue/inputswitch'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'

import TeamsCardLarge from '../components/teams/TeamsCardLarge.vue'
import TeamsCardSmall from '../components/teams/TeamsCardSmall.vue'
import TeamsDataTable from '../components/teams/TeamsDataTable.vue'
import { hasPermission } from '../lib/permissions'

const COOKIE_KEY = 'ui_teams_view'
const VALID_VIEWS = ['large','small','list']
const view = ref('large')
const viewOptions = [
  { label: 'crop_landscape', value: 'large' },
  { label: 'view_cozy', value: 'small' },
  { label: 'table_rows', value: 'list' }
]

const showInactive = ref(false)

const teams = ref([])
const loading = ref(false)

const canModify = computed(() => hasPermission('TEAMS.MODIFY'))

async function fetchTeams() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/teams')
    if (!resp.ok) throw new Error('Failed to load teams')
    teams.value = await resp.json()
  } finally {
    loading.value = false
  }
}

const visibleTeams = computed(() => {
  if (showInactive.value) return teams.value
  return teams.value.filter(t => !t.inactive)
})

// Edit dialog
const editDialogVisible = ref(false)
const editModel = ref({ id: null, name: '', inactive: false })

function openAdd() {
  editModel.value = { id: null, name: '', inactive: false }
  editDialogVisible.value = true
}
function openEdit(team) {
  editModel.value = { ...team }
  editDialogVisible.value = true
}

async function saveEdit() {
  const isNew = !editModel.value.id
  const payload = { id: editModel.value.id || undefined, name: editModel.value.name, inactive: !!editModel.value.inactive }
  const url = isNew ? '/api/v1/teams' : `/api/v1/teams/${encodeURIComponent(editModel.value.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchTeams()
}

onMounted(async () => {
  await fetchTeams()
})
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Teams'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <!-- Toolbar -->
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Teams</div>
            <div class="flex align-items-center gap-2">
              <div class="flex align-items-center gap-2">
                <span class="text-sm text-700">Show inactive</span>
                <InputSwitch v-model="showInactive" />
              </div>
              <SelectButton v-model="view" :options="viewOptions" optionValue="value" optionLabel="label">
                <template #option="{ option }">
                  <span class="material-symbols-outlined">{{ option.label }}</span>
                </template>
              </SelectButton>
              <Button v-if="canModify" label="Add Team" icon="pi pi-plus" @click="openAdd" />
            </div>
          </div>

          <!-- Content panel -->
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <div v-if="view === 'large'" class="cards-grid cards-grid-large">
              <TeamsCardLarge v-for="t in visibleTeams" :key="t.id" :team="t" :canModify="canModify" @edit="openEdit" />
            </div>
            <div v-else-if="view === 'small'" class="cards-grid cards-grid-small">
              <TeamsCardSmall v-for="t in visibleTeams" :key="t.id" :team="t" :canModify="canModify" @edit="openEdit" />
            </div>
            <div v-else>
              <TeamsDataTable :teams="visibleTeams" :canModify="canModify" @edit="openEdit" />
            </div>
          </div>

          <Dialog v-model:visible="editDialogVisible" modal header="Team" :style="{ width: '500px' }">
            <div class="flex flex-column gap-3">
              <div>
                <label class="block mb-1 text-sm">Name</label>
                <InputText v-model="editModel.name" class="w-full" />
              </div>
              <div class="flex gap-2 align-items-center">
                <Checkbox inputId="inactive" v-model="editModel.inactive" :binary="true" />
                <label for="inactive">Inactive</label>
              </div>
              <div class="flex justify-content-end gap-2">
                <Button label="Cancel" text @click="editDialogVisible = false" />
                <Button v-if="canModify" label="Save" icon="pi pi-check" @click="saveEdit" />
              </div>
            </div>
          </Dialog>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cards-grid {
  display: grid;
  grid-auto-rows: minmax(0, auto);
  gap: .5rem;
}
/* Large view: up to 2 per row */
.cards-grid-large {
  grid-template-columns: 1fr;
}
@media (min-width: 768px) {
  .cards-grid-large { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
/* Small view: up to 4 per row */
.cards-grid-small {
  grid-template-columns: 1fr 1fr;
}
@media (min-width: 768px) {
  .cards-grid-small { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 1100px) {
  .cards-grid-small { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
</style>
