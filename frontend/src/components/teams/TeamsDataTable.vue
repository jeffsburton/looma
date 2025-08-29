<script setup>
import { ref, computed, watch } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import AvatarGroup from 'primevue/avatargroup'
import Avatar from 'primevue/avatar'

const props = defineProps({
  teams: { type: Array, default: () => [] },
  canModify: { type: Boolean, default: false }
})

const rows = ref(10)
const filterText = ref('')

const filtered = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return props.teams
  return props.teams.filter(t => [t.name].some(v => (v || '').toLowerCase().includes(q)))
})

const emit = defineEmits(['edit'])
</script>

<template>
  <div>
    <div class="flex align-items-center justify-content-end mb-2">
      <span class="p-input-icon-left">
        <i class="pi pi-search" />
        <InputText v-model="filterText" placeholder="Filter..." />
      </span>
    </div>

    <DataTable
      :value="filtered"
      paginator
      :rows="rows"
      :rowsPerPageOptions="[10,20,50]"
      removableSort
      dataKey="id"
      class="p-datatable-sm"
    >
      <Column header="" style="width:3.5rem">
        <template #body="{ data }">
          <img v-if="data.photo_url" :src="data.photo_url" alt="avatar" style="width:28px;height:28px;border-radius:999px;object-fit:cover" />
        </template>
      </Column>
      <Column field="name" header="Name" sortable></Column>
      <Column field="event_name" header="Event" sortable>
        <template #body="{ data }">
          <span>{{ data.event_name || '' }}</span>
        </template>
      </Column>
      <Column header="Cases">
        <template #body="{ data }">
          <AvatarGroup v-if="data.cases && data.cases.length" class="gap-1">
            <Avatar v-for="(c, i) in data.cases" :key="c.id || i" :image="c.photo_url" shape="circle" style="width:24px;height:24px" v-tooltip.top="c.name" />
          </AvatarGroup>
          <span v-else class="text-600">—</span>
        </template>
      </Column>
      <Column header="Members">
        <template #body="{ data }">
          <AvatarGroup v-if="data.members && data.members.length" class="gap-1">
            <Avatar v-for="(m, i) in data.members" :key="m.id || i" :image="m.photo_url" shape="circle" style="width:24px;height:24px" v-tooltip.top="m.name" />
          </AvatarGroup>
          <span v-else class="text-600">—</span>
        </template>
      </Column>
      <Column field="inactive" header="Inactive" sortable>
        <template #body="{ data }">
          <i v-if="data.inactive" class="pi pi-check" />
        </template>
      </Column>
      <Column header="Actions" style="width:8rem">
        <template #body="{ data }">
          <Button v-if="canModify" icon="pi pi-pencil" size="small" text @click="$emit('edit', data)" />
        </template>
      </Column>
    </DataTable>
  </div>
</template>
