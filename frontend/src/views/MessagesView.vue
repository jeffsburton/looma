<script setup>
import { ref, onMounted } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import api from '../lib/api'
import Messages from '../components/Messages.vue'
import UnseenMessageCount from "@/components/common/UnseenMessageCount.vue";

const rows = ref([])
const loading = ref(false)

async function loadData() {
  loading.value = true
  try {
    // Load cases for selection
    const casesResp = await api.get('/api/v1/cases/select', { headers: { Accept: 'application/json' } })
    const items = Array.isArray(casesResp.data) ? casesResp.data : []

    // Prepare base rows
    const baseRows = items.map(it => ({
      id: it.id, // opaque id
      rawId: it.raw_db_id, // internal only for mapping; never displayed
      name: it.name,
      photoUrl: it.photo_url,
      caseNumber: it.case_number,
      teamsText: '',
      teams: [], // [{ name, photoUrl }]
    }))

    // Build a map raw case id -> index in rows for quick update
    const idxByRaw = new Map()
    baseRows.forEach((r, idx) => {
      if (typeof r.rawId === 'number') idxByRaw.set(r.rawId, idx)
    })

    // Load teams to derive case -> team names and photos mapping (best available bulk source)
    // Note: TeamRead.cases contains raw case ids; used only for client-side mapping.
    try {
      const teamsResp = await api.get('/api/v1/teams', { headers: { Accept: 'application/json' } })
      const teams = Array.isArray(teamsResp.data) ? teamsResp.data : []
      // Map case raw id -> [{ name, photoUrl }]
      const caseTeams = new Map()
      for (const t of teams) {
        const tname = t?.name
        const tphoto = t?.photo_url || '/images/pfp-generic.png'
        const tcases = Array.isArray(t?.cases) ? t.cases : []
        for (const c of tcases) {
          const cid = typeof c?.id === 'number' ? c.id : undefined
          if (cid == null) continue
          if (!caseTeams.has(cid)) caseTeams.set(cid, [])
          caseTeams.get(cid).push({ name: tname, photoUrl: tphoto })
        }
      }
      // Fill teamsText and teams list on baseRows
      for (const [cid, teamsArr] of caseTeams.entries()) {
        const idx = idxByRaw.get(cid)
        if (idx != null) {
          baseRows[idx].teams = teamsArr
          baseRows[idx].teamsText = teamsArr.map(t => t?.name).filter(Boolean).join(', ')
        }
      }
    } catch (_) {
      // Teams may be restricted by permission; ignore gracefully
    }

    rows.value = baseRows
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})

const expandedRows = ref({});

</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Messages'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="surface-card border-round p-2 flex-1 overflow-auto">


            <!-- Cases list for Messages context -->
            <DataTable :value="rows" dataKey="id" v-model:expandedRows="expandedRows"
                       size="small"  :loading="loading" class="w-full">
              <Column expander style="width: 5rem" />
              <Column header="" style="width:48px">
                <template #body="{ data }">
                  <UnseenMessageCount TableName="case" :CaseId="data.id">
                    <img :src="data.photoUrl" :alt="data.name" class="avatar" />
                  </UnseenMessageCount>
                </template>
              </Column>
              <Column field="name" header="Name" />
              <Column field="caseNumber" header="Case #" style="width:140px" />
              <Column header="Teams">
                <template #body="{ data }">
                  <div class="teams-cell">
                    <template v-if="Array.isArray(data.teams) && data.teams.length">
                      <div class="team-avatars">
                        <img v-for="(t, i) in data.teams" :key="i" :src="t.photoUrl" :alt="t.name" :title="t.name" class="team-avatar" />
                      </div>
                      <span class="teams-text">{{ data.teamsText }}</span>
                    </template>
                    <template v-else>
                      <span>—</span>
                    </template>
                  </div>
                </template>
              </Column>
              <template #expansion="slotProps">
                <div>
                  <Messages :caseId="slotProps.data.id"/>
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
.teams-cell { display: flex; align-items: center; gap: .5rem; }
.team-avatars { display: flex; align-items: center; gap: 4px; }
.team-avatar { width: 18px; height: 18px; border-radius: 999px; object-fit: cover; border: 1px solid rgba(0,0,0,0.1); }
</style>
