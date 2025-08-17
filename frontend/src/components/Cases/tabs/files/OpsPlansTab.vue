<script setup>
import { ref } from 'vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'

// Local data model for Ops Plans. In the future, lift to store/API as needed.
const nextId = ref(1)
const expandedRows = ref([])

const plans = ref([
  {
    id: nextId.value++,
    date: '11/20/2025',
    purpose: 'Knock&Talk',
    location: '3827 Hermes Ave',
    // Expanded form fields
    weather: 'Sunny, 84 deg',
    opType: null,
    agency: 'ARYS',
    briefingTime: '7:00am',
    rendevouz: '3829 Alexander',
    comms: '4',
    synopsis: 'Go to the door and knock. '
  }
])

const opTypeOptions = [
  { label: 'Search', value: 'search' },
  { label: 'Canvass', value: 'canvass' },
  { label: 'Briefing', value: 'briefing' },
  { label: 'Lead Follow-up', value: 'lead' },
  { label: 'Other', value: 'other' }
]

const weatherOptions = [
  { label: 'Clear', value: 'clear' },
  { label: 'Cloudy', value: 'cloudy' },
  { label: 'Rain', value: 'rain' },
  { label: 'Snow', value: 'snow' },
  { label: 'Windy', value: 'windy' }
]

function addRow() {
  plans.value.push({
    id: nextId.value++,
    date: '',
    purpose: '',
    location: '',
    weather: '',
    opType: null,
    agency: '',
    briefingTime: '',
    rendevouz: '',
    comms: '',
    synopsis: ''
  })
}

function removeRow(rowId) {
  plans.value = plans.value.filter(p => p.id !== rowId)
  // Remove from expandedRows for both array- and object-shaped states
  const er = expandedRows.value
  if (Array.isArray(er)) {
    expandedRows.value = er.filter(r => r.id !== rowId)
  } else if (er && typeof er === 'object') {
    // In object mode, keys are dataKey values
    const copy = { ...er }
    delete copy[rowId]
    expandedRows.value = copy
  }
  if (plans.value.length === 0) addRow()
}

function rowClass(data) {
  // Highlight the header row when its expansion is open
  const er = expandedRows.value
  const isExpanded = Array.isArray(er)
    ? er.some(r => r.id === data.id)
    : !!(er && typeof er === 'object' && er[data.id])
  return isExpanded ? 'expanded-row-highlight' : ''
}
</script>

<template>
  <div class="p-3">

    <div class="flex justify-content-end mb-2">
      <Button label="Add Plan" icon="pi pi-plus" @click="addRow" size="small" />
    </div>

    <DataTable
      :value="plans"
      dataKey="id"
      v-model:expandedRows="expandedRows"
      :rowClass="rowClass"
      stripedRows
      size="small"
      class="shadow-1 border-round surface-card"
      tableStyle="min-width: 40rem"
    >
      <Column expander style="width: 3rem" />

      <Column field="date" header="Date" style="min-width: 10rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.date || '—' }}</span>
        </template>
      </Column>

      <Column field="purpose" header="Purpose" style="min-width: 14rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.purpose || '—' }}</span>
        </template>
      </Column>

      <Column field="location" header="Location" style="min-width: 14rem">
        <template #body="{ data }">
          <span class="text-800">{{ data.location || '—' }}</span>
        </template>
      </Column>

      <Column header="" style="width:6rem">
        <template #body="{ data }">
          <Button icon="pi pi-trash" severity="danger" text rounded @click="removeRow(data.id)" />
        </template>
      </Column>

      <template #expansion="{ data }">
        <div class="p-3 surface-section border-round">
          <div class="grid formgrid p-fluid">
            <!-- Top summary fields match table columns -->
            <div class="col-12 md:col-4">
              <label class="block mb-2">Date</label>
              <InputText v-model="data.date" placeholder="YYYY-MM-DD" />
            </div>
            <div class="col-12 md:col-4">
              <label class="block mb-2">Purpose</label>
              <InputText v-model="data.purpose" placeholder="Purpose of operation" />
            </div>
            <div class="col-12 md:col-4">
              <label class="block mb-2">Location</label>
              <InputText v-model="data.location" placeholder="Location" />
            </div>

            <!-- Required form fields -->
            <div class="col-12 md:col-3">
              <label class="block mb-2">Weather</label>
              <Dropdown v-model="data.weather" :options="weatherOptions" optionLabel="label" optionValue="value" placeholder="Select weather" class="w-full" />
            </div>
            <div class="col-12 md:col-3">
              <label class="block mb-2">Op Type</label>
              <Dropdown v-model="data.opType" :options="opTypeOptions" optionLabel="label" optionValue="value" placeholder="Select type" class="w-full" />
            </div>
            <div class="col-12 md:col-3">
              <label class="block mb-2">Agency</label>
              <InputText v-model="data.agency" placeholder="Agency name" />
            </div>
            <div class="col-12 md:col-3">
              <label class="block mb-2">Briefing Time</label>
              <InputText v-model="data.briefingTime" placeholder="HH:MM" />
            </div>

            <div class="col-12 md:col-6">
              <label class="block mb-2">Rendevouz</label>
              <InputText v-model="data.rendevouz" placeholder="Rendezvous location" />
            </div>
            <div class="col-12 md:col-6">
              <label class="block mb-2">Comms Channel</label>
              <InputText v-model="data.comms" placeholder="Radio/Comms details" />
            </div>

            <div class="col-12">
              <label class="block mb-2">Synopsis</label>
              <Textarea v-model="data.synopsis" auto-resize rows="3" placeholder="Brief synopsis of the plan" />
            </div>
          </div>
        </div>
      </template>
    </DataTable>
  </div>
</template>

<style scoped>
/* Highlight the main row whenever its expansion is open */
:deep(.expanded-row-highlight) {
  background-color: var(--p-surface-200, #eef2f7);
  transition: background-color .2s ease-in-out;
}
</style>
