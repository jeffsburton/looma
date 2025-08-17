<script setup>
import { ref } from 'vue'
import SelectButton from 'primevue/selectbutton'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

// Calendar components and styles
import { CalendarView, CalendarViewHeader } from 'vue-simple-calendar'
import 'vue-simple-calendar/dist/vue-simple-calendar.css'
import 'vue-simple-calendar/dist/css/default.css'
import 'vue-simple-calendar/dist/css/holidays-us.css'

// Toggle between list and calendar
const mode = ref('list')
const modeOptions = [
  { label: 'list', value: 'list' },
  { label: 'calendar_month', value: 'calendar' }
]

// Sample timeline entries (placeholder data)
const items = ref([
  { id: 1, date: '2025-08-12', time: '09:30', who: 'Officer Lee', what: 'Interview', where: 'LVPD HQ', details: 'Initial interview with guardian.' },
  { id: 2, date: '2025-08-13', time: '14:00', who: 'Case Worker', what: 'Home Visit', where: '123 Palm St', details: 'Checked bedroom and belongings.' },
  { id: 3, date: '2025-08-15', time: '11:15', who: 'Neighbor', what: 'Witness Statement', where: 'Apt 4B', details: 'Saw subject on corner store 8/14 7pm.' },
])

// Calendar state
const showDate = ref(new Date())
function setShowDate(d) { showDate.value = d }
</script>

<template>
  <div class="p-3 panel">
    <!-- Top bar with view toggle -->
    <div class="flex align-items-center justify-content-between gap-2 pb-2">
      <div class="text-lg font-semibold flex align-items-center gap-2">
        <span class="material-symbols-outlined">timeline</span>
        <span>Timeline</span>
      </div>
      <SelectButton v-model="mode" :options="modeOptions" optionValue="value" optionLabel="label">
        <template #option="{ option }">
          <span class="material-symbols-outlined">{{ option.label }}</span>
        </template>
      </SelectButton>
    </div>

    <!-- Content -->
    <div class="surface-card border-round p-2 flex-1 overflow-auto">
      <!-- List View -->
      <DataTable v-if="mode === 'list'" :value="items" dataKey="id" stripedRows size="small" class="w-full" tableStyle="min-width: 40rem">
        <Column field="date" header="Date" sortable />
        <Column field="time" header="Time" sortable />
        <Column field="who" header="Who" sortable />
        <Column field="what" header="What" sortable />
        <Column field="where" header="Where" sortable />
        <Column field="details" header="Details" />
      </DataTable>

      <!-- Calendar View -->
      <div v-else class="calendar-container">
        <CalendarView
            :show-date="showDate"
            class="theme-default holiday-us-traditional holiday-us-official">

        </CalendarView>
      </div>
    </div>
  </div>
</template>

<style scoped>
.panel { display: flex; flex-direction: column; height: 100%; }
.calendar-container { height: 67vh; /* similar to example */ }
/* Ensure calendar fills container width */
.calendar-container :deep(.cv-wrapper) { width: 100%; height: 100%; }
</style>
