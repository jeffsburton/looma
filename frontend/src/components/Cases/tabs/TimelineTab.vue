<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import Divider from 'primevue/divider'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import SelectButton from 'primevue/selectbutton'
import Popover from 'primevue/popover'
import { getLocaleDateFormat } from '../../../lib/util.js'


// Calendar components and styles
import { CalendarView, CalendarViewHeader } from 'vue-simple-calendar'
import 'vue-simple-calendar/dist/vue-simple-calendar.css'
import 'vue-simple-calendar/dist/css/default.css'
import 'vue-simple-calendar/dist/css/holidays-us.css'

import CaseSubjectSelect from '../CaseSubjectSelect.vue'
import DatePicker from "primevue/datepicker";

const props = defineProps({
  caseId: { type: String, default: '' },
  primarySubject: { type: Object, default: null },
})

const loading = ref(false)
const error = ref('')
const rows = ref([])

// View selector for list/calendar-week/calendar-month
const view = ref('list')
const viewOptions = [
  { label: 'table_rows', value: 'list' },
  { label: 'view_week', value: 'calendar_week' },
  { label: 'calendar_month', value: 'calendar_month' },
]
const calendarUom = computed(() => (view.value === 'calendar_week' ? 'week' : 'month'))

// Calendar state
const showDate = ref(new Date())
function setShowDate(d) { showDate.value = d }

const earliestDate = computed(() => {
  const dates = (rows.value || [])
    .map(r => r?.date)
    .filter(Boolean)
    .map(d => new Date(d))
    .filter(d => !isNaN(d.getTime()))
  if (!dates.length) return null
  return new Date(Math.min(...dates.map(d => d.getTime())))
})
const showDateInitialized = ref(false)
watch([rows, earliestDate], () => {
  if (!showDateInitialized.value && earliestDate.value) {
    showDate.value = earliestDate.value
    showDateInitialized.value = true
  }
})

// Calendar items mapping
const calendarItems = computed(() => {
  return (rows.value || []).map(e => ({
    id: e.id,
    startDate: e.date ? new Date(e.date + (e.time ? " " + e.time : "")) : null,
    endDate: e.date ? new Date(e.date) : null,
    title: e.details || e.type_id || 'Event',
    classes: [e.id.replace(/[^a-zA-Z0-9]/g, '')
]
  })).filter(it => it.startDate)
})

// Popover for calendar item click
const pop = ref()
const popTarget = ref()
const selectedItem = ref(null)
function onClickItem(payload) {
  console.log(payload)
  const item = payload && payload.item ? payload.item : payload
  const id = item && (item.id ?? item.key ?? item.value)
  const row = (rows.value || []).find(r => String(r.id) === String(id))
  selectedItem.value = row || null

  if (!pop?.value) return

  // Prefer anchoring to the actual clicked calendar item element
  let els = document.getElementsByClassName(payload.id.replace(/[^a-zA-Z0-9]/g, ''))
  let anchorEl = els.length ? els[0] : null

  if (anchorEl) {
    pop.value.hide()
    // Align popover to the real item element
    nextTick(() => {
      pop.value.show({ currentTarget: anchorEl, target: anchorEl })
    })
  }
}

function sortKey(r) {
  const dateStr = r?.date ? (typeof r.date === 'string' ? r.date : fmtDate(r.date)) : null
  const timeStr = r?.time ? (typeof r.time === 'string' ? r.time : fmtTime(r.time)) : null
  // Prefix: '0' for rows with a date (sort first), '1' for rows without a date (sort last)
  const prefix = dateStr ? '0' : '1'
  if (!dateStr) {
    // Keep a stable order among undated items by id
    const idPart = String(r?.id ?? '').padStart(12, '0')
    return `${prefix}|~|${idPart}`
  }
  const dd = String(dateStr).padStart(10, '0')
  const tt = String(timeStr || '').padStart(8, '0')
  return `${prefix}|${dd}T${tt}`
}

const sortedRows = computed(() => {
  return [...rows.value].sort((a, b) => {
    const ka = sortKey(a)
    const kb = sortKey(b)
    return ka.localeCompare(kb)
  })
})

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/timeline`
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (!resp.ok) throw new Error('Failed to load timeline')
    rows.value = await resp.json()
    // Reset calendar initial date on reload
    showDateInitialized.value = false
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load timeline.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

function fmtDate(val) {
  if (val == null || val === '') return null
  if (typeof val === 'string') return val
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return null
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  } catch { return null }
}
function fmtTime(val) {
  if (val == null || val === '') return null
  if (typeof val === 'string') return val
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return null
    const hh = String(d.getHours()).padStart(2, '0')
    const mm = String(d.getMinutes()).padStart(2, '0')
    const ss = String(d.getSeconds()).padStart(2, '0')
    return `${hh}:${mm}:${ss}`
  } catch { return null }
}
async function patchRow(row, patch) {
  if (!row?.id || !props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/timeline/${encodeURIComponent(String(row.id))}`
    const payload = { ...patch }
    if (Object.prototype.hasOwnProperty.call(payload, 'date')) {
      payload.date = fmtDate(payload.date)
    }
    if (Object.prototype.hasOwnProperty.call(payload, 'time')) {
      payload.time = fmtTime(payload.time)
    }
    const resp = await fetch(url, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!resp.ok) throw new Error('Failed to save change')
  } catch (e) {
    console.error(e)
    load()
  }
}

async function addRow() {
  if (!props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/timeline`
    const payload = {}
    const resp = await fetch(url, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
    if (!resp.ok) console.error('Failed to create timeline row')
  } catch (e) {
    console.error(e)
  } finally {
    await load()
  }
}
</script>

<template>
  <div class="p-2 flex flex-column gap-2" style="min-height: 400px;">
    <div class="flex align-items-center justify-content-between">
      <div />
      <SelectButton v-model="view" :options="viewOptions" optionValue="value" optionLabel="label">
        <template #option="{ option }">
          <span class="material-symbols-outlined">{{ option.label }}</span>
        </template>
      </SelectButton>
    </div>

    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <div v-if="loading" class="p-2 text-600">Loading...</div>

    <!-- Calendar view -->
    <div v-else-if="view === 'calendar_week' || view === 'calendar_month'" class="calendar-container">
      <CalendarView
        :items="calendarItems"
        :show-date="showDate"
        @click-item="onClickItem"
        :display-period-uom="calendarUom"
        class="theme-default holiday-us-traditional holiday-us-official"
      >
        <template #header="{ headerProps }">
          <calendar-view-header slot="header" :header-props="headerProps" @input="setShowDate" />
        </template>
      </CalendarView>
      <!-- Invisible anchor element used to position the Popover -->
      <span ref="popTarget" style="position: fixed; left: -9999px; top: -9999px; width: 0; height: 0; pointer-events: none;"></span>
      <Popover ref="pop">
        <div v-if="selectedItem" class="p-2 text-sm">
          <div class="mb-1 font-medium">Timeline Item</div>
          <div><span class="text-600">Date:</span> <span class="text-900">{{ selectedItem.date || '—' }}</span></div>
          <div v-if="selectedItem.time"><span class="text-600">Time:</span> <span class="text-900">{{ selectedItem.time }}</span></div>
          <div v-if="selectedItem.who_display || selectedItem.who_name"><span class="text-600">Who:</span> <span class="text-900">{{ selectedItem.who_display || selectedItem.who_name }}</span></div>
          <div v-if="selectedItem.where"><span class="text-600">Where:</span> <span class="text-900">{{ selectedItem.where }}</span></div>
          <div v-if="selectedItem.details"><span class="text-600">Details:</span> <span class="text-900">{{ selectedItem.details }}</span></div>
        </div>
      </Popover>
    </div>

    <!-- List (existing) view -->
    <div v-else class="cards">
      <template v-for="(data, idx) in sortedRows" :key="data.id">
        <div class="card surface-card border-round p-1">
          <div class="flex flex-column gap-1">

            <div class="form-grid">
              <!-- Date -->
              <div class="field" style="min-width: 10px;max-width: 120px">
                <template v-if="data.rule_out">
                  <label class="block text-sm text-600">Date</label>
                  <div :style="'text-decoration: line-through;'">{{ data.date || '—' }}</div>
                </template>
                <template v-else>
                  <FloatLabel variant="on">
                    <DatePicker v-model="data.date" :date-format="getLocaleDateFormat()" class="" @update:modelValue="(v) => patchRow(data, { date: v || null })"  />
                    <label>Date</label>
                  </FloatLabel>
                </template>
              </div>

              <!-- Time -->
              <div class="field" style="min-width: 10px;max-width: 120px">
                <template v-if="data.rule_out">
                  <label class="block text-sm text-600">Time</label>
                  <div :style="'text-decoration: line-through;'">{{ data.time || '—' }}</div>
                </template>
                <template v-else>
                  <FloatLabel variant="on">
                    <DatePicker v-model="data.time" class="w-full" @update:modelValue="(v) => patchRow(data, { time: v || null })" timeOnly hourFormat="24" showTime />
                    <label>Time</label>
                  </FloatLabel>
                </template>
              </div>

              <!-- Who -->
              <div class="field" style="min-width: 10px;max-width: 250px">
                <template v-if="data.rule_out">
                  <label class="block text-sm text-600">Who</label>
                  <div :style="'text-decoration: line-through;'">{{ data.who_name || data.who_display || '—' }}</div>
                </template>
                <template v-else>
                  <FloatLabel variant="on">
                    <CaseSubjectSelect style="max-width: 250px" v-model="data.who_id" :caseId="caseId" :primarySubject="primarySubject" @change="(v) => patchRow(data, { who_id: v })" />
                    <label>Who</label>
                  </FloatLabel>
                </template>
              </div>

              <!-- Where -->
              <div class="field">
                <template v-if="data.rule_out">
                  <label class="block text-sm text-600">Where</label>
                  <div :style="'text-decoration: line-through;'">{{ data.where || '—' }}</div>
                </template>
                <template v-else>
                  <FloatLabel variant="on" class="w-full">
                    <InputText v-model="data.where" class="w-full" @change="() => patchRow(data, { where: data.where || null })" />
                    <label>Where</label>
                  </FloatLabel>
                </template>
              </div>

              <!-- Details -->
              <div class="field">
                <template v-if="data.rule_out">
                  <label class="block text-sm text-600">Details</label>
                  <div :style="'text-decoration: line-through;'">{{ data.details || '—' }}</div>
                </template>
                <template v-else>
                  <FloatLabel variant="on" class="w-full">
                    <InputText v-model="data.details" class="w-full" @change="() => patchRow(data, { details: data.details || null })" />
                    <label>Details</label>
                  </FloatLabel>
                </template>
              </div>

              <div class="field">
                <div class="flex align-items-center gap-2 nowrap">
                  <label class="text-sm text-600">Rule Out</label>
                  <ToggleSwitch v-model="data.rule_out" @update:modelValue="(v) => patchRow(data, { rule_out: v })" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <Divider v-if="idx < sortedRows.length - 1" class="my-1 divider" />
      </template>

    </div>
      <div class="mt-2 flex ">
        <Button label="Add" size="small" icon="pi pi-plus" @click="addRow" />
      </div>
  </div>
</template>

<style scoped>
.cards { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: flex-start; }
.card { flex: 0 0 auto; width: auto; max-width: 100%; }
.form-grid { display: flex; flex-wrap: wrap; gap: 0.25rem 0.5rem; }
.field { min-width: 12rem; }
:deep(.p-divider) { margin: 0.25rem 0; }
@media (max-width: 640px) { .field { min-width: 100%; } }

/* Calendar container: grow to fill */
.calendar-container { display: flex; flex-direction: column; flex: 1 1 auto; min-height: 400px; }
.calendar-container :deep(.cv-wrapper) { width: 100%; height: 100%; }
</style>
