<script setup>
import { ref, onMounted, computed } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import ToggleSwitch from 'primevue/toggleswitch'
import api from '../lib/api'
import Messages from '../components/Messages.vue'
import UnseenMessageCount from "@/components/common/UnseenMessageCount.vue";

// Data
const rows = ref([]) // flat list of tasks across all accessible cases
const loading = ref(false)
const expandedRows = ref({})
const showCompleted = ref(false) // default off similar to TasksTab

// People cache for "Assigned by"
const personMap = ref({})
const personsLoaded = ref(false)
async function loadPersonsOnce() {
  if (personsLoaded.value) return
  try {
    const { data } = await api.get('/api/v1/persons/select', { params: { shepherds: true, non_shepherds: true } })
    const map = {}
    const arr = Array.isArray(data) ? data : []
    for (const p of arr) {
      if (p && p.id) {
        map[p.id] = {
          id: p.id,
          name: p.name || 'Unknown',
          photo_url: p.photo_url || '/images/pfp-generic.png',
        }
      }
    }
    personMap.value = map
  } finally {
    personsLoaded.value = true
  }
}
function getPerson(opaqueId) {
  if (!opaqueId) return null
  return personMap.value[opaqueId] || null
}

// Load cases, then tasks per case
async function loadData() {
  loading.value = true
  try {
    const casesResp = await api.get('/api/v1/cases/select', { headers: { Accept: 'application/json' } })
    const cases = Array.isArray(casesResp.data) ? casesResp.data : []

    const allRows = []
    for (const c of cases) {
      const caseId = c?.id
      if (!caseId) continue
      try {
        const resp = await api.get(`/api/v1/cases/${encodeURIComponent(caseId)}/tasks`, { headers: { Accept: 'application/json' } })
        const tasks = Array.isArray(resp.data) ? resp.data : []
        for (const t of tasks) {
          allRows.push({
            id: t.id,
            caseId: caseId,
            caseName: c?.name,
            casePhotoUrl: c?.photo_url || '/images/pfp-generic.png',
            caseNumber: c?.case_number,
            assigned_by_id: t.assigned_by_id,
            title: t.title,
            description: t.description,
            ready_for_review: !!t.ready_for_review,
            completed: !!t.completed,
          })
        }
      } catch (_) {
        // This case might be inaccessible for tasks; ignore and continue
      }
    }

    // Sort similar to backend default: non-completed first, then ready_for_review, then id
    allRows.sort((a, b) => {
      if (a.completed !== b.completed) return a.completed ? 1 : -1
      if (a.ready_for_review !== b.ready_for_review) return a.ready_for_review ? -1 : 1
      const ai = String(a.id)
      const bi = String(b.id)
      return ai.localeCompare(bi)
    })

    rows.value = allRows
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPersonsOnce()
  loadData()
})

const displayedRows = computed(() => {
  const arr = Array.isArray(rows.value) ? rows.value : []
  return showCompleted.value ? arr : arr.filter(r => !r.completed)
})
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Tasks'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="surface-card border-round p-2 flex-1 overflow-auto">

            <!-- Toolbar: show completed toggle only (no add; cross-case) -->
            <div class="flex gap-2 align-items-center flex-wrap mb-3">
              <div class="flex align-items-center gap-2">
                <ToggleSwitch id="showCompletedTasks" v-model="showCompleted" />
                <label for="showCompletedTasks">Show completed</label>
              </div>
            </div>

            <DataTable :value="displayedRows" dataKey="id" v-model:expandedRows="expandedRows"
                       size="small" :loading="loading" class="w-full">
              <Column expander style="width: 3rem" />

              <!-- Task icon with unseen count -->
              <Column header="" style="width:48px">
                <template #body="{ data }">
                  <UnseenMessageCount TableName="task" :CaseId="data.caseId" :TaskId="data.id">
                    <div class="flex align-items-center">
                      <span class="material-symbols-outlined text-900 font-medium">assignment</span>
                    </div>
                  </UnseenMessageCount>
                </template>
              </Column>

              <!-- Case info: avatar + name -->
              <Column header="Case">
                <template #body="{ data }">
                  <div class="flex align-items-center gap-2">
                    <img :src="data.casePhotoUrl" :alt="data.caseName" class="avatar" />
                    <span class="text-900 font-medium name-clip">{{ data.caseName }}</span>
                  </div>
                </template>
              </Column>

              <!-- Case number -->
              <Column field="caseNumber" header="Case #" style="width:140px" />

              <!-- Assigned by -->
              <Column header="Assigned by">
                <template #body="{ data }">
                  <div class="flex align-items-center gap-2">
                    <img :src="getPerson(data.assigned_by_id)?.photo_url || '/images/pfp-generic.png'" alt="pfp" class="avatar-sm" />
                    <span class="text-900 font-medium name-clip">{{ getPerson(data.assigned_by_id)?.name || 'Unknown' }}</span>
                  </div>
                </template>
              </Column>

              <!-- Task title -->
              <Column field="title" header="Title" />

              <!-- Task description -->
              <Column field="description" header="Description" />

              <!-- Status columns -->
              <Column header="Ready for review" style="width:160px">
                <template #body="{ data }">
                  <span v-if="data.ready_for_review" class="material-symbols-outlined text-yellow-200" title="Ready for review">hand_gesture</span>
                  <span v-else>—</span>
                </template>
              </Column>
              <Column header="Completed" style="width:130px">
                <template #body="{ data }">
                  <span v-if="data.completed" class="material-symbols-outlined text-green-600" title="Completed">check_circle</span>
                  <span v-else>—</span>
                </template>
              </Column>

              <!-- Expansion shows messages filtered to this task within its case -->
              <template #expansion="slotProps">
                <div>
                  <p>Ask questions, provide updates here:</p>
                  <Messages :caseId="slotProps.data.caseId" filterByFieldName="task_id" :filterByFieldId="slotProps.data.id" />
                </div>
              </template>
            </DataTable>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.avatar { width: 32px; height: 32px; border-radius: 999px; object-fit: cover; }
.avatar-sm { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.name-clip { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
