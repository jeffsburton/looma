<script setup>
import { ref, watch } from 'vue'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import DatePicker from 'primevue/datepicker'

import RefSelect from '../../RefSelect.vue'
import Divider from "primevue/divider";
import {getLocaleDateFormat} from "../../../lib/util.js";

const props = defineProps({
  caseId: { type: String, default: '' },
})

const loading = ref(false)
const error = ref('')
const rows = ref([])

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/activity`
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (!resp.ok) throw new Error('Failed to load activity')
    rows.value = await resp.json()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load activity.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

async function patchRow(row, patch) {
  if (!row?.id || !props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/activity/${encodeURIComponent(String(row.id))}`
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
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/activity`
    const resp = await fetch(url, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    if (!resp.ok) console.error('Failed to create activity row')
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

    <template v-for="(data, idx) in rows" :key="data.id">
      <div class="surface-card border-round p-1">
        <div class="flex flex-column gap-1">
          <div class="form-grid">
            <!-- Date -->
            <div class="field w-12 md:w-2" style="min-width: 10px;max-width: 140px">
              <template v-if="data.rule_out">
                <label class="block text-sm text-600">Date</label>
                <div :style="'text-decoration: line-through;'">{{ data.date || '—' }}</div>
              </template>
              <template v-else>
                <FloatLabel variant="on">
                  <DatePicker :date-format="getLocaleDateFormat()" v-model="data.date" class="w-full" @change="() => patchRow(data, { date: data.date || null })" />
                  <label>Date</label>
                </FloatLabel>
              </template>
            </div>

            <!-- Source -->
            <div class="field" style="min-width: 250px;max-width: 250px">
              <template v-if="data.rule_out">
                <label class="block text-sm text-600">Source</label>
                <div :style="'text-decoration: line-through;'">{{ data.source_name || data.source_other || '—' }}</div>
              </template>
              <template v-else>
                <FloatLabel variant="on">
                  <RefSelect
                    code="ACT_SOURCE"
                    v-model="data.source_id"
                    :currentCode="data.source_code || ''"
                    :otherValue="data.source_other || ''"
                    @update:otherValue="(v) => { data.source_other = v }"
                    @otherCommit="(v) => patchRow(data, { source_other: v || null })"
                    @change="(v) => patchRow(data, { source_id: v })"
                  />
                  <label>Source</label>
                </FloatLabel>
              </template>
            </div>

            <!-- Reported To -->
            <div class="field" style="min-width: 250px;max-width: 250px">
              <template v-if="data.rule_out">
                <label class="block text-sm text-600">Reported To</label>
                <div :style="'text-decoration: line-through;'">{{ data.reported_to_name || data.reported_to_other || '—' }}</div>
              </template>
              <template v-else>
                <FloatLabel variant="on">
                  <RefSelect
                    code="ACT_REP"
                    v-model="data.reported_to"
                    :currentCode="data.reported_to_code || ''"
                    :otherValue="data.reported_to_other || ''"
                    @update:otherValue="(v) => { data.reported_to_other = v }"
                    @otherCommit="(v) => patchRow(data, { reported_to_other: v || null })"
                    @change="(v) => patchRow(data, { reported_to: v })"
                  />
                  <label>Reported To</label>
                </FloatLabel>
              </template>
            </div>

            <!-- What -->
            <div class="field">
              <template v-if="data.rule_out">
                <label class="block text-sm text-600">What</label>
                <div :style="'text-decoration: line-through;'">{{ data.what || '—' }}</div>
              </template>
              <template v-else>
                <FloatLabel variant="on" class="w-full">
                  <Textarea v-model="data.what" autoResize rows="2" class="w-full" @change="() => patchRow(data, { what: data.what || null })" />
                  <label>What</label>
                </FloatLabel>
              </template>
            </div>

            <!-- Findings -->
            <div class="field">
              <template v-if="data.rule_out">
                <label class="block text-sm text-600">Findings</label>
                <div :style="'text-decoration: line-through;'">{{ data.findings || '—' }}</div>
              </template>
              <template v-else>
                <FloatLabel variant="on" class="w-full">
                  <Textarea v-model="data.findings" autoResize rows="2" class="w-full" @change="() => patchRow(data, { findings: data.findings || null })" />
                  <label>Findings</label>
                </FloatLabel>
              </template>
            </div>

            <!-- Case Management -->
            <div class="field">
              <template v-if="data.rule_out">
                <label class="block text-sm text-600">Case Management</label>
                <div :style="'text-decoration: line-through;'">{{ data.case_management || '—' }}</div>
              </template>
              <template v-else>
                <FloatLabel variant="on" class="w-full">
                  <Textarea v-model="data.case_management" autoResize rows="2" class="w-full" @change="() => patchRow(data, { case_management: data.case_management || null })" />
                  <label>Case Management</label>
                </FloatLabel>
              </template>
            </div>



            <!-- On EOD Report & Rule Out -->
            <div class="field">
              <div class="flex align-items-center gap-3">
                <div class="flex align-items-center gap-2 nowrap">
                  <label class="text-sm text-600  text-right" style="max-width: 70px;">On EOD Report</label>
                  <ToggleSwitch v-model="data.on_eod_report" @update:modelValue="(v) => patchRow(data, { on_eod_report: v })" />
                </div>
                <div class="flex align-items-center gap-2 nowrap">
                  <label class="text-sm text-600  text-right" style="max-width: 50px">Rule Out</label>
                  <ToggleSwitch v-model="data.rule_out" @update:modelValue="(v) => patchRow(data, { rule_out: v })" />
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>
        <Divider  class="my-1 divider" />
    </template>

    <div class="mt-2">
      <Button label="Add" size="small" icon="pi pi-plus" @click="addRow" />
    </div>
  </div>
</template>

<style scoped>
.form-grid { display: flex; flex-wrap: wrap; gap: 0.25rem 0.5rem; }
.field { min-width: 12rem; }
:deep(.p-divider) { margin: 0.25rem 0; }
@media (max-width: 640px) { .field { min-width: 100%; } }
</style>
