<script setup>
import { ref, watch, computed } from 'vue'
import Fieldset from 'primevue/fieldset'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import ToggleSwitch from 'primevue/toggleswitch'
import Textarea from 'primevue/textarea'

import RefSelect from '../../../RefSelect.vue'
import SubjectPanel from '../../../contacts/Subject.vue'

const props = defineProps({
  caseId: { type: String, default: '' }, // opaque case id; may be empty initially until case loads
})

const loading = ref(false)
const error = ref('')
const rows = ref([]) // [{ id, relationship_id, relationship_name, relationship_code, relationship_other, legal_guardian, notes, rule_out, subject: {...} }]

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/subjects`
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (!resp.ok) throw new Error('Failed to load subjects')
    rows.value = await resp.json()
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load investigatory subjects.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

async function patchRow(row, patch) {
  if (!row?.id || !props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/subjects/${encodeURIComponent(String(row.id))}`
    const resp = await fetch(url, {
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch),
    })
    if (!resp.ok) throw new Error('Failed to save change')
    // No need to reload; optimistic UI already updated
  } catch (e) {
    console.error(e)
    // On error, reload row list to resync
    load()
  }
}

// Subject dialog
const editVisible = ref(false)
const editingSubject = ref(null)
function openEdit(row) {
  if (row?.rule_out) return // hidden when rule_out anyway
  editingSubject.value = {
    id: row.subject.id,
    first_name: row.subject.first_name,
    last_name: row.subject.last_name,
    nicknames: row.subject.nicknames,
    phone: row.subject.phone,
    email: row.subject.email,
    dangerous: row.subject.dangerous,
    danger: row.subject.danger,
  }
  editVisible.value = true
}
function onEdited() {
  // refresh subject names/flags
  load()
}

// Helpers for static render
function yesNo(v) { return v ? 'Yes' : 'No' }
function relationshipDisplay(row) {
  const code = String(row.relationship_code || '').toUpperCase()
  if (code === 'OTH' && row.relationship_other) return row.relationship_other
  return row.relationship_name || '—'
}

function telHref(val) {
  if (!val) return ''
  const digits = String(val).trim().replace(/[^+\d]/g, '')
  return `tel:${digits}`
}
</script>

<template>
  <div class="p-2 flex flex-column gap-3">
    <Fieldset legend="Investigatory Subjects">
      <div v-if="error" class="p-error mb-2">{{ error }}</div>
      <DataTable :value="rows" :loading="loading" dataKey="id" size="small" stripedRows :paginator="false" class="border-round surface-card">
        <Column header="" style="width: 3rem;">
          <template #body="{ data }">
            <Button v-if="!data.rule_out" icon="pi pi-pencil" text rounded @click="openEdit(data)" :title="`Edit ${data.subject.first_name} ${data.subject.last_name}`" />
          </template>
        </Column>
        <Column header="First Name" sortable>
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.subject.first_name }}</span>
          </template>
        </Column>
        <Column header="Last Name" sortable>
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.subject.last_name }}</span>
          </template>
        </Column>
        <Column header="">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.subject.nicknames }}</span>
          </template>
        </Column>
        <Column header="Phone">
          <template #body="{ data }">
            <template v-if="data.subject.phone">
              <a :href="telHref(data.subject.phone)" class="link-row" :style="data.rule_out ? 'text-decoration: line-through;' : ''" @click.stop>
                <span class="icon">📞</span>
                <span class="text">{{ data.subject.phone }}</span>
              </a>
            </template>
            <span v-else class="text-600">—</span>
          </template>
        </Column>
        <Column header="Relationship">
          <template #body="{ data }">
            <template v-if="data.rule_out">
              <span :style="'text-decoration: line-through;'">{{ relationshipDisplay(data) }}</span>
            </template>
            <template v-else>
              <div class="min-w-12rem" style="max-width: 16rem;">
                <RefSelect
                  code="SUB_REL"
                  v-model="data.relationship_id"
                  :currentCode="data.relationship_code || ''"
                  :otherValue="data.relationship_other || ''"
                  @update:otherValue="(v) => { data.relationship_other = v }"
                  @otherCommit="(v) => patchRow(data, { relationship_other: v || null })"
                  @change="(v) => patchRow(data, { relationship_id: v })"
                />
              </div>
            </template>
          </template>
        </Column>
        <Column header="Legal Guardian" style="width: 10rem;">
          <template #body="{ data }">
            <template v-if="data.rule_out">
              <span :style="'text-decoration: line-through;'">{{ yesNo(!!data.legal_guardian) }}</span>
            </template>
            <template v-else>
              <ToggleSwitch v-model="data.legal_guardian" @update:modelValue="(v) => patchRow(data, { legal_guardian: v })" />
            </template>
          </template>
        </Column>
        <Column header="Notes" style="min-width: 18rem;">
          <template #body="{ data }">
            <template v-if="data.rule_out">
              <span :style="'text-decoration: line-through;'">{{ data.notes || '—' }}</span>
            </template>
            <template v-else>
              <Textarea v-model="data.notes" autoResize rows="1" class="w-full" @change="() => patchRow(data, { notes: data.notes || null })" />
            </template>
          </template>
        </Column>
        <Column header="Rule Out" style="width: 8rem;">
          <template #body="{ data }">
            <ToggleSwitch v-model="data.rule_out" @update:modelValue="(v) => patchRow(data, { rule_out: v })" />
          </template>
        </Column>
      </DataTable>
    </Fieldset>

    <Fieldset legend="Agency Personnel">
      <div class="text-600 p-2">No content yet.</div>
    </Fieldset>

    <Dialog v-model:visible="editVisible" modal header="Edit Subject" :style="{ width: '640px' }">
      <SubjectPanel v-if="editingSubject" v-model="editingSubject" :isNew="false" :canModify="true" @updated="onEdited" @avatarChanged="onEdited" />
      <template #footer>
        <Button label="Close" text @click="editVisible=false" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.min-w-12rem { min-width: 12rem; }
.link-row { display: inline-flex; align-items: center; gap: .35rem; text-decoration: none; color: inherit; }
.link-row:hover .text { text-decoration: underline; }
.icon { width: 1em; display: inline-flex; align-items: center; justify-content: center; }
a.icon, a.icon:hover, a.icon:focus { text-decoration: none; color: inherit; }
</style>
