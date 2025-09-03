<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Dialog from 'primevue/dialog'
import DatePicker from 'primevue/datepicker'
import Checkbox from 'primevue/checkbox'
import FloatLabel from 'primevue/floatlabel'
import SelectButton from 'primevue/selectbutton'
import RefSelect from '../components/RefSelect.vue'
import { hasPermission } from '../lib/permissions'
import { getCookie, setCookie } from '../lib/cookies'

// Calendar components and styles for calendar view
import { CalendarView, CalendarViewHeader } from 'vue-simple-calendar'
import 'vue-simple-calendar/dist/vue-simple-calendar.css'
import 'vue-simple-calendar/dist/css/default.css'
import 'vue-simple-calendar/dist/css/holidays-us.css'

const events = ref([])
const loading = ref(false)
const filterText = ref('')

// View selector: cards, calendar, list
const COOKIE_KEY = 'ui_events_view'
const VALID_VIEWS = ['cards','calendar','list']
const view = ref('cards')
try {
  const v = getCookie(COOKIE_KEY)
  const val = (v || '').toString()
  if (VALID_VIEWS.includes(val)) view.value = val
} catch {}
const viewOptions = [
  { label: 'crop_landscape', value: 'cards' },
  { label: 'calendar_month', value: 'calendar' },
  { label: 'table_rows', value: 'list' }
]

// Calendar state
const showDate = ref(new Date())
function setShowDate(d) { showDate.value = d }

const editDialogVisible = ref(false)
const editModel = reactive({
  id: null,
  name: '',
  short_name: '',
  description: '',
  city: '',
  state_id: '',
  state_code: '',
  start: null,
  end: null,
  inactive: false,
})

const canModify = computed(() => hasPermission('EVENTS.MODIFY'))

// Validation state
const errors = reactive({
  name: '',
  short_name: '',
  description: '',
})
const validationMessage = ref('')

function clearErrors() {
  for (const k of Object.keys(errors)) errors[k] = ''
  validationMessage.value = ''
}

function validate() {
  clearErrors()
  let ok = true
  if (!editModel.name || !String(editModel.name).trim()) {
    errors.name = 'Name is required.'
    ok = false
  }
  if (!editModel.short_name || !String(editModel.short_name).trim()) {
    errors.short_name = 'Short Name is required.'
    ok = false
  } else if (String(editModel.short_name).length > 10) {
    errors.short_name = 'Short Name must be 10 characters or fewer.'
    ok = false
  }
  if (!editModel.description || !String(editModel.description).trim()) {
    errors.description = 'Description is required.'
    ok = false
  } else if (String(editModel.description).length > 200) {
    errors.description = 'Description must be 200 characters or fewer.'
    ok = false
  }
  if (!ok) {
    validationMessage.value = 'Please correct the highlighted fields.'
  }
  return ok
}

const filteredEvents = computed(() => {
  const q = filterText.value.trim().toLowerCase()
  if (!q) return events.value
  return events.value.filter((o) => [o.name, o.short_name, o.city, o.state_code].some((v) => (v || '').toLowerCase().includes(q)))
})

// Long date formatting for card view
const longDateFmt = new Intl.DateTimeFormat(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
function toLongDate(val) {
  if (!val) return ''
  try {
    const d = typeof val === 'string' ? new Date(val) : val
    if (isNaN(d?.getTime?.())) return String(val)
    return longDateFmt.format(d)
  } catch { return String(val) }
}

// Calendar items mapping
const calendarItems = computed(() => {
  return (events.value || []).map(e => ({
    id: e.id,
    startDate: e.start ? new Date(e.start) : null,
    endDate: e.end ? new Date(e.end) : null,
    title: e.short_name || e.name || 'Event',
    classes: e.inactive ? ['cv-item-inactive'] : []
  })).filter(it => it.startDate)
})

async function fetchEvents() {
  loading.value = true
  try {
    const resp = await fetch('/api/v1/events')
    if (!resp.ok) throw new Error('Failed to load events')
    events.value = await resp.json()
  } finally {
    loading.value = false
  }
}

function openAdd() {
  Object.assign(editModel, { id: null, name: '', short_name: '', description: '', city: '', state_id: '', state_code: '', start: null, end: null, inactive: false })
  clearErrors()
  editDialogVisible.value = true
}

function openEdit(row) {
  Object.assign(editModel, { ...row })
  clearErrors()
  editDialogVisible.value = true
}

function onClickItem(payload) {
  if (!canModify.value) return
  // vue-simple-calendar may send the item directly or inside an object as { item, originalEvent }
  const item = payload && payload.item ? payload.item : payload
  const id = item && (item.id ?? item.key ?? item.value)
  if (!id) return
  const row = (events.value || []).find(ev => String(ev.id) === String(id))
  if (row) {
    openEdit(row)
  }
}

async function saveEdit() {
  if (!validate()) return
  const payload = {
    id: editModel.id || undefined,
    name: editModel.name,
    short_name: editModel.short_name,
    description: editModel.description,
    city: editModel.city || '',
    state_id: editModel.state_id || null,
    start: editModel.start || null,
    end: editModel.end || null,
    inactive: !!editModel.inactive,
  }
  const isNew = !editModel.id
  const url = isNew ? '/api/v1/events' : `/api/v1/events/${encodeURIComponent(editModel.id)}`
  const method = isNew ? 'POST' : 'PUT'
  const resp = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err?.detail || 'Save failed')
  }
  editDialogVisible.value = false
  await fetchEvents()
}

onMounted(async () => {
  await fetchEvents()
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
          <SidebarMenu :active="'Events'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Events</div>
            <div class="flex align-items-center gap-2">
              <SelectButton v-model="view" :options="viewOptions" optionValue="value" optionLabel="label">
                <template #option="{ option }">
                  <span class="material-symbols-outlined">{{ option.label }}</span>
                </template>
              </SelectButton>
            </div>
          </div>

          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <div class="flex align-items-center justify-content-between mb-2 gap-2">
              <div />
              <div class="flex gap-2">
                <span class="p-input-icon-left">
                  <i class="pi pi-search" />
                  <InputText v-model="filterText" placeholder="Filter..." />
                </span>
                <Button v-if="canModify" label="Add" icon="pi pi-plus" @click="openAdd" />
              </div>
            </div>

            <!-- Cards view -->
            <div v-if="view === 'cards'" class="cards-grid cards-grid-large">
              <div v-for="e in filteredEvents" :key="e.id" class="event-card p-2 border-1 surface-border border-round">
                <div class="flex align-items-center justify-content-between gap-2 mb-1">
                  <div class="font-semibold text-lg text-900 flex align-items-center gap-2">
                    <span>{{ e.name }}</span>
                    <span v-if="e.short_name" class="px-2 py-1 text-xs border-round surface-200 text-800">{{ e.short_name }}</span>
                  </div>
                  <div class="flex align-items-center gap-2">
                    <span v-if="e.inactive" class="text-600 text-sm">Inactive</span>
                    <Button v-if="canModify" icon="pi pi-pencil" size="small" text @click="openEdit(e)" />
                  </div>
                </div>
                <div class="text-700 text-sm mb-2">
                  <span v-if="e.city">{{ e.city }}</span>
                  <span v-if="e.city && e.state_code">, </span>
                  <span v-if="e.state_code">{{ e.state_code }}</span>
                </div>
                <div class="flex flex-column gap-1 text-sm">
                  <div><span class="text-700">Start:</span> <span class="text-900">{{ toLongDate(e.start) }}</span></div>
                  <div><span class="text-700">End:</span> <span class="text-900">{{ toLongDate(e.end) }}</span></div>
                </div>
              </div>
            </div>

            <!-- Calendar view -->
            <div v-else-if="view === 'calendar'" class="calendar-container">
              <CalendarView
                :items="calendarItems"
                :show-date="showDate"
                @click-item="onClickItem"
                display-period-uom="month"
                class="theme-default holiday-us-traditional holiday-us-official"
              >
                <template #header="{ headerProps }">
                  <calendar-view-header slot="header" :header-props="headerProps" @input="setShowDate" />
                </template>
              </CalendarView>
            </div>

            <!-- List (table) view -->
            <DataTable
              v-else
              :value="filteredEvents"
              dataKey="id"
              :loading="loading"
              paginator
              :rows="10"
              :rowsPerPageOptions="[10,20,50]"
              removableSort
              class="p-datatable-sm"
              stripedRows
            >
              <Column field="name" header="Name" sortable></Column>
              <Column field="short_name" header="Short Name" sortable></Column>
              <Column field="city" header="City" sortable></Column>
              <Column field="state_code" header="State" sortable></Column>
              <Column field="start" header="Start" sortable>
                <template #body="{ data }">
                  <span>{{ data.start || '' }}</span>
                </template>
              </Column>
              <Column field="end" header="End" sortable>
                <template #body="{ data }">
                  <span>{{ data.end || '' }}</span>
                </template>
              </Column>
              <Column field="inactive" header="Inactive" sortable>
                <template #body="{ data }">
                  <i v-if="data.inactive" class="pi pi-check" />
                </template>
              </Column>
              <Column header="Actions" style="width:8rem">
                <template #body="{ data }">
                  <Button v-if="canModify" icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
                </template>
              </Column>
            </DataTable>

            <Dialog v-model:visible="editDialogVisible" modal header="Event" :style="{ width: '600px' }">
              <div class="flex flex-column gap-3 mt-1">
                <div v-if="validationMessage" class="text-red-600 text-sm">{{ validationMessage }}</div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <FloatLabel variant="on">
                      <label class="block mb-1 text-sm">Name</label>
                      <InputText v-model="editModel.name" :class="['w-full', errors.name && 'p-invalid']" />
                    </FloatLabel>
                    <small v-if="errors.name" class="p-error text-red-600">{{ errors.name }}</small>
                  </div>
                  <div class="flex-1" style="max-width: 220px;">
                    <FloatLabel variant="on">
                    <label class="block mb-1 text-sm">Short Name</label>
                    <InputText v-model="editModel.short_name" :class="['w-full', errors.short_name && 'p-invalid']" maxlength="10" />
                    </FloatLabel>
                    <small v-if="errors.short_name" class="p-error text-red-600">{{ errors.short_name }}</small>
                  </div>
                </div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <FloatLabel variant="on">
                    <label class="block mb-1 text-sm">City</label>
                    <InputText v-model="editModel.city" class="w-full" />
                    </FloatLabel>
                  </div>
                  <div class="flex-1">
                    <FloatLabel variant="on">
                    <RefSelect v-model="editModel.state_id" code="STATE" :showCode="true" :currentCode="editModel.state_code" :add="false" placeholder="Select state..." />
                    <label class="block mb-1 text-sm">State</label>
                    </FloatLabel>
                  </div>
                </div>
                <div class="flex gap-2">
                  <div class="flex-1">
                    <FloatLabel variant="on">
                    <DatePicker v-model="editModel.start" dateFormat="yy-mm-dd" showIcon iconDisplay="input" />
                    <label class="block mb-1 text-sm">Start</label>
                    </FloatLabel>
                  </div>
                  <div class="flex-1">
                    <FloatLabel variant="on">
                    <DatePicker v-model="editModel.end" dateFormat="yy-mm-dd" showIcon iconDisplay="input" />
                    <label class="block mb-1 text-sm">End</label>
                    </FloatLabel>
                  </div>
                </div>
                <div>
                    <FloatLabel variant="on">
                  <label class="block mb-1 text-sm">Description</label>
                  <textarea v-model="editModel.description" rows="4" maxlength="200" class="w-full p-inputtext"></textarea>
                    </FloatLabel>
                  <small v-if="errors.description" class="p-error text-red-600">{{ errors.description }}</small>
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
  </div>
</template>

<style scoped>
/* Card grid styles similar to Teams */
.cards-grid {
  display: grid;
  grid-auto-rows: minmax(0, auto);
  gap: .5rem;
}
.cards-grid-large { grid-template-columns: 1fr; }
@media (min-width: 768px) {
  .cards-grid-large { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* Calendar container height */
.calendar-container { display: flex;
flex-direction: column;
flex-grow: 1; }
.calendar-container :deep(.cv-wrapper) { width: 100%; height: 100%; }
</style>
