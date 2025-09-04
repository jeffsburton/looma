<script setup>
import { ref, watch, computed } from 'vue'
import Divider from 'primevue/divider'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'

import CaseSubjectSelect from '../CaseSubjectSelect.vue'
import DatePicker from "primevue/datepicker";

const props = defineProps({
  caseId: { type: String, default: '' },
  primarySubject: { type: Object, default: null },
})

const loading = ref(false)
const error = ref('')
const rows = ref([])

function sortKey(r) {
  const d = r?.date || ''
  const t = r?.time || ''
  const dd = String(d || '').padStart(10, '0')
  const tt = String(t || '').padStart(8, '0')
  return `${dd}T${tt}`
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
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load timeline.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

async function patchRow(row, patch) {
  if (!row?.id || !props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/timeline/${encodeURIComponent(String(row.id))}`
    const resp = await fetch(url, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
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
  <div class="p-2 flex flex-column gap-1">
    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <div v-if="loading" class="p-2 text-600">Loading...</div>

    <div class="cards">
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
                    <DatePicker v-model="data.date" class="" @change="() => patchRow(data, { date: data.date || null })"  />
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
                    <DatePicker v-model="data.time" class="w-full" @change="() => patchRow(data, { time: data.time || null })" timeOnly hourFormat="24" showTime />
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

    <div class="mt-2 flex justify-content-end">
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
</style>
