<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'

// Local data for Activity entries (can be lifted to a store/API later)
const nextId = ref(1)
const activities = ref([
  {
    id: nextId.value++,
    date: '2025-08-17',
    source: 'Tip Line',
    regarding: 'Sighting near 5th & Main',
    findings: 'Caller reported possible match; patrol checked area with negative results.'
  }
])

function addRow() {
  activities.value.push({
    id: nextId.value++,
    date: '',
    source: '',
    regarding: '',
    findings: ''
  })
}

function removeRow(rowId) {
  activities.value = activities.value.filter(a => a.id !== rowId)
  if (activities.value.length === 0) addRow()
}
</script>
<template>
  <div class="p-3">
    <div class="text-lg font-semibold mb-3 flex align-items-center gap-2">
      <span class="material-symbols-outlined">skateboarding</span>
      <span>Activity</span>
    </div>

    <div class="flex justify-content-end mb-2">
      <Button label="Add Activity" icon="pi pi-plus" @click="addRow" size="small" />
    </div>

    <DataTable
      :value="activities"
      dataKey="id"
      stripedRows
      size="small"
      class="shadow-1 border-round surface-card"
      tableStyle="min-width: 40rem"
    >
      <Column field="date" header="Date" style="min-width: 10rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.date || '—' }}</span>
        </template>
      </Column>

      <Column field="source" header="Source" style="min-width: 12rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.source || '—' }}</span>
        </template>
      </Column>

      <Column field="regarding" header="Regarding" style="min-width: 16rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.regarding || '—' }}</span>
        </template>
      </Column>

      <Column field="findings" header="Findings" style="min-width: 24rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.findings || '—' }}</span>
        </template>
      </Column>

      <Column header="" style="width:6rem">
        <template #body="{ data }">
          <Button icon="pi pi-trash" severity="danger" text rounded @click="removeRow(data.id)" />
        </template>
      </Column>
    </DataTable>


  </div>
</template>
