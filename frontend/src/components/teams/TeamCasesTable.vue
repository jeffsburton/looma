<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import FloatLabel from 'primevue/floatlabel'
import CaseSelect from '../CaseSelect.vue'

const props = defineProps({
  teamId: { type: String, required: true }, // opaque team id
  cases: { type: Array, default: () => [] }, // [{ id (case numeric), name, photo_url }]
  canModify: { type: Boolean, default: false },
})

const emit = defineEmits(['changed'])

const newCaseId = ref('')

async function addCase(caseOpaqueId) {
  if (!props.canModify) return
  if (!caseOpaqueId || !props.teamId) return
  const url = `/api/v1/teams/${encodeURIComponent(props.teamId)}/cases`
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ case_id: caseOpaqueId })
  })
  if (!resp.ok) {
    console.error('Failed to add case')
    return
  }
  newCaseId.value = ''
  emit('changed')
}

async function deleteCase(caseId) {
  if (!props.canModify) return
  if (!caseId || !props.teamId) return
  const url = `/api/v1/teams/${encodeURIComponent(props.teamId)}/cases/${encodeURIComponent(caseId)}`
  const resp = await fetch(url, { method: 'DELETE' })
  if (!resp.ok) {
    console.error('Failed to delete case')
    return
  }
  emit('changed')
}
</script>

<template>
  <div>
    <DataTable :value="cases" size="small" dataKey="id" :rows="10" :paginator="cases?.length > 10">
      <Column header="" style="width:48px">
        <template #body="{ data }">
          <img :src="data.photo_url" :alt="data.name" class="avatar" />
        </template>
      </Column>
      <Column field="name" header="Name" />
      <Column header="" style="width:56px">
        <template #body="{ data }">
          <button v-if="canModify" class="icon-button" title="Remove" @click="deleteCase(data.id)">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </template>
      </Column>
    </DataTable>

    <div v-if="canModify" class="mt-2">
      <FloatLabel variant="on">
        <CaseSelect
          v-model="newCaseId"
          @change="(v) => v && addCase(v)"
        />
        <label>Add case</label>
      </FloatLabel>
    </div>
  </div>
</template>

<style scoped>
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; }
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.06); }
</style>
