<script setup>
import { ref, watch, computed } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import RefSelect from '../RefSelect.vue'
import Button from 'primevue/button'

const props = defineProps({
  teamId: { type: String, required: true }, // opaque team id
  members: { type: Array, default: () => [] }, // [{ id (person numeric), name, photo_url, role_id, role_code, role_name }]
  canModify: { type: Boolean, default: false },
})

const emit = defineEmits(['changed'])

async function updateRole(personId, newRoleId) {
  if (!props.canModify) return
  if (!personId || !props.teamId || !newRoleId) return
  const url = `/api/v1/teams/${encodeURIComponent(props.teamId)}/members/${encodeURIComponent(personId)}`
  const resp = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ team_role_id: newRoleId })
  })
  if (!resp.ok) {
    console.error('Failed to update role')
    return
  }
  emit('changed')
}

async function deleteMember(personId) {
  if (!props.canModify) return
  if (!personId || !props.teamId) return
  const url = `/api/v1/teams/${encodeURIComponent(props.teamId)}/members/${encodeURIComponent(personId)}`
  const resp = await fetch(url, { method: 'DELETE' })
  if (!resp.ok) {
    console.error('Failed to delete member')
    return
  }
  emit('changed')
}
</script>

<template>
  <div>
    <DataTable :value="members" size="small" dataKey="id" :rows="10" :paginator="members?.length > 10">
      <Column header="" style="width:48px">
        <template #body="{ data }">
          <img :src="data.photo_url" :alt="data.name" class="avatar" />
        </template>
      </Column>
      <Column field="name" header="Name" />
      <Column header="Role">
        <template #body="{ data }">
          <RefSelect
            code="TEAM_ROLE"
            v-model="data.role_id"
            :currentCode="data.role_code"
            :disabled="!canModify"
            :showCode="false"
            placeholder="Select role"
            @change="(v) => updateRole(data.id, v)"
          />
        </template>
      </Column>
      <Column header="" style="width:56px">
        <template #body="{ data }">
          <button v-if="canModify" class="icon-button" title="Remove" @click="deleteMember(data.id)">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<style scoped>
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; }
.icon-button { background: transparent; border: none; padding: .25rem; cursor: pointer; border-radius: 4px; }
.icon-button:hover { background: rgba(0,0,0,0.06); }
</style>
