<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import SidebarMenu from '../components/SidebarMenu.vue'
import SelectButton from 'primevue/selectbutton'
import ToggleSwitch from 'primevue/toggleswitch'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Checkbox from 'primevue/checkbox'
import AvatarEditor from '../components/common/AvatarEditor.vue'
import EventSelect from '../components/EventSelect.vue'

import TeamsCardLarge from '../components/teams/TeamsCardLarge.vue'
import TeamsCardSmall from '../components/teams/TeamsCardSmall.vue'
import TeamsDataTable from '../components/teams/TeamsDataTable.vue'
import TeamMembersTable from '../components/teams/TeamMembersTable.vue'
import TeamCasesTable from '../components/teams/TeamCasesTable.vue'
import { hasPermission } from '../lib/permissions'
import { getCookie, setCookie } from '../lib/cookies'
import FloatLabel from "primevue/floatlabel";

const route = useRoute()
const router = useRouter()

const COOKIE_KEY = 'ui_teams_view'
const VALID_VIEWS = ['large','small','list']
const view = ref('large')
// Restore view from cookie if valid
try {
  const v = getCookie(COOKIE_KEY)
  const val = (v || '').toString()
  if (VALID_VIEWS.includes(val)) view.value = val
} catch {}
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

// Sorted list for card views (large/small) by team name
const sortedVisibleTeams = computed(() => {
  const arr = visibleTeams.value || []
  // Create a shallow copy before sorting to avoid mutating source
  return [...arr].sort((a, b) => String(a?.name || '').localeCompare(String(b?.name || ''), undefined, { sensitivity: 'base' }))
})

// Query-driven edit mode
const editModel = ref({ id: null, name: '', inactive: false, event_id: '' })
const contentRef = ref(null)
const savedScrollTop = ref(0)
const suppressAutoSave = ref(false)
let autoSaveTimer = null

const currentTeam = computed(() => {
  const id = editModel.value.id
  if (!id) return null
  return teams.value.find(x => String(x.id) === String(id)) || null
})

const isEditMode = computed(() => !!route.query.team)

function goToListAndRestore() {
  // remove only 'team' from query, keep others
  const { team, ...rest } = route.query
  router.replace({ name: 'teams', query: { ...rest } })
}

function openAdd() {
  router.replace({ name: 'teams', query: { ...route.query, team: 'new' } })
}
function openEdit(team) {
  const id = team?.id || ''
  router.replace({ name: 'teams', query: { ...route.query, team: id } })
}

async function updateExisting() {
  const payload = { id: editModel.value.id, name: editModel.value.name, inactive: !!editModel.value.inactive, event_id: (editModel.value.event_id ?? '') }
  const url = `/api/v1/teams/${encodeURIComponent(editModel.value.id)}`
  const resp = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
}

async function saveEdit() {
  const isNew = !editModel.value.id
  const payload = { id: editModel.value.id || undefined, name: editModel.value.name, inactive: !!editModel.value.inactive, event_id: (editModel.value.event_id ?? '') }
  const url = isNew ? '/api/v1/teams' : `/api/v1/teams/${encodeURIComponent(editModel.value.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  await fetchTeams()
  goToListAndRestore()
}

const onAvatarChanged = async () => {
  // Refresh teams to update photo_url in lists
  await fetchTeams()
}

// Populate edit model when route query or teams change
watch(
  () => [route.query.team, teams.value],
  async () => {
    const q = route.query.team
    if (!q) return
    suppressAutoSave.value = true
    if (q === 'new') {
      editModel.value = { id: null, name: '', inactive: false, event_id: '' }
      await nextTick()
      suppressAutoSave.value = false
      return
    }
    const t = teams.value.find(x => String(x.id) === String(q))
    if (t) {
      editModel.value = { id: t.id, name: t.name, inactive: !!t.inactive, event_id: t.event_id || '' }
    }
    await nextTick()
    suppressAutoSave.value = false
  },
  { immediate: true }
)

// Auto-save for existing teams on field changes (debounced)
watch(
  () => ({ id: editModel.value.id, name: editModel.value.name, inactive: !!editModel.value.inactive, event_id: editModel.value.event_id || '' }),
  async (val, oldVal) => {
    if (!val.id) return // only when editing existing team
    if (suppressAutoSave.value) return
    if (!canModify.value) return
    if (autoSaveTimer) clearTimeout(autoSaveTimer)
    autoSaveTimer = setTimeout(async () => {
      try {
        await updateExisting()
        await fetchTeams()
      } catch (e) {
        // Optionally could surface an error toast; ignoring to keep minimal UI changes
        console.error('Auto-save failed', e)
      }
    }, 400)
  },
  { deep: true }
)

// Save/restore scroll when toggling edit mode
watch(isEditMode, async (val, oldVal) => {
  const el = contentRef.value
  if (!el) return
  if (val && !oldVal) {
    savedScrollTop.value = el.scrollTop
  } else if (!val && oldVal) {
    await nextTick()
    el.scrollTop = savedScrollTop.value || 0
  }
})

onMounted(async () => {
  await fetchTeams()
})

// Persist view changes to cookie
watch(view, (val) => {
  try {
    if (!VALID_VIEWS.includes(val)) return
    setCookie(COOKIE_KEY, val, { maxAge: 60 * 60 * 24 * 365, sameSite: 'Lax' })
  } catch {}
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
                <ToggleSwitch v-model="showInactive" />
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
          <div ref="contentRef" class="surface-card border-round p-2 flex-1 overflow-auto">
            <!-- List mode -->
            <template v-if="!isEditMode">
              <div v-if="view === 'large'" class="cards-grid cards-grid-large">
                <TeamsCardLarge v-for="t in sortedVisibleTeams" :key="t.id" :team="t" :canModify="canModify" @edit="openEdit" />
              </div>
              <div v-else-if="view === 'small'" class="cards-grid cards-grid-small">
                <TeamsCardSmall v-for="t in sortedVisibleTeams" :key="t.id" :team="t" :canModify="canModify" @edit="openEdit" />
              </div>
              <div v-else>
                <TeamsDataTable :teams="visibleTeams" :canModify="canModify" @edit="openEdit" />
              </div>
            </template>

            <!-- Edit mode -->
            <template v-else>
              <div class="flex align-items-center gap-2 mb-3">
                <button class="icon-button" @click="goToListAndRestore" title="Back">
                  <span class="material-symbols-outlined">arrow_back</span>
                </button>
                <div class="text-lg font-semibold">{{ editModel.id ? 'Edit Team' : 'New Team' }}</div>
              </div>
              <div class="flex flex-column gap-3" style="max-width:560px;">
                <div>
                  <FloatLabel variant="on">
                    <label class="block mb-1 text-sm">Name</label>
                    <InputText v-model="editModel.name" class="w-full" />
                </FloatLabel>
                </div>
                <div>
                  <FloatLabel variant="on">
                    <EventSelect v-model="editModel.event_id" :disabled="!canModify" placeholder="Select event" />
                    <label class="block mb-1 text-sm">Event</label>
                </FloatLabel>
                </div>
                <div class="flex gap-2 align-items-center">
                  <Checkbox inputId="inactive" v-model="editModel.inactive" :binary="true" />
                  <label for="inactive">Inactive</label>
                </div>
                <div v-if="editModel.id && canModify" class="flex align-items-center">
                  <label class="block mb-1 text-sm" style="min-width: 100px;">Profile Picture</label>
                  <AvatarEditor kind="team" :id="editModel.id" :size="48" @changed="onAvatarChanged" />
                </div>

                <div v-if="editModel.id">
                  <div class="text-800 font-semibold mb-2">Members</div>
                  <TeamMembersTable
                    :teamId="editModel.id"
                    :members="currentTeam?.members || []"
                    :canModify="canModify"
                    @changed="fetchTeams"
                  />
                </div>

                <div v-if="editModel.id">
                  <div class="text-800 font-semibold mb-2 mt-4">Cases</div>
                  <TeamCasesTable
                    :teamId="editModel.id"
                    :cases="currentTeam?.cases || []"
                    :canModify="canModify"
                    @changed="fetchTeams"
                  />
                </div>

                <div v-if="!editModel.id" class="flex justify-content-end gap-2">
                  <Button label="Cancel" text @click="goToListAndRestore" />
                  <Button v-if="canModify" label="Create" icon="pi pi-check" @click="saveEdit" />
                </div>
              </div>
            </template>
          </div>
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
  grid-template-columns: 1fr;
}
@media (min-width: 768px) {
  .cards-grid-small { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 1100px) {
  .cards-grid-small { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.04); }
</style>
