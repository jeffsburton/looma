<script setup>
import { ref, watch } from 'vue'
import Divider from 'primevue/divider'
import Button from 'primevue/button'
import ToggleSwitch from 'primevue/toggleswitch'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'

import RefSelect from '../../RefSelect.vue'
import CasePersonSelect from '../CasePersonSelect.vue'
import PersonSelect from '../../PersonSelect.vue'

const props = defineProps({
  caseId: { type: String, default: '' },
  primarySubject: { type: Object, default: null },
})

const loading = ref(false)
const error = ref('')
const rows = ref([])

function href(val) {
  const s = String(val || '').trim()
  if (!s) return ''
  if (/^https?:\/\//i.test(s)) return s
  try {
    const u = new URL('http://example.com')
  } catch {}
  return s.startsWith('http') ? s : `https://${s}`
}

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media`
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (!resp.ok) throw new Error('Failed to load social media')
    const baseRows = await resp.json()
    // initialize aliases array
    rows.value = baseRows.map(r => ({ ...r, aliases: [], _aliasesLoading: true }))
    // Load aliases for each row in parallel
    await Promise.all(rows.value.map(async (r) => {
      try {
        const aurl = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(r.id))}/aliases`
        const aresp = await fetch(aurl, { credentials: 'include', headers: { 'Accept': 'application/json' } })
        r.aliases = aresp.ok ? (await aresp.json()) : []
      } catch {
        r.aliases = []
      } finally {
        r._aliasesLoading = false
      }
    }))
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load social media.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

async function addAlias(row) {
  if (!props.caseId || !row?.id) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(row.id))}/aliases`
    const resp = await fetch(url, { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
    if (!resp.ok) console.error('Failed to create alias')
  } catch (e) {
    console.error(e)
  } finally {
    await loadAliases(row)
  }
}

async function loadAliases(row) {
  if (!props.caseId || !row?.id) return
  row._aliasesLoading = true
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(row.id))}/aliases`
    const resp = await fetch(url, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    row.aliases = resp.ok ? (await resp.json()) : []
  } catch (e) {
    console.error(e)
    row.aliases = []
  } finally {
    row._aliasesLoading = false
  }
}

async function patchAlias(row, alias, patch) {
  if (!props.caseId || !row?.id || !alias?.id) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(row.id))}/aliases/${encodeURIComponent(String(alias.id))}`
    const resp = await fetch(url, { method: 'PATCH', credentials: 'include', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) })
    if (!resp.ok) throw new Error('Failed to save alias change')
  } catch (e) {
    console.error(e)
    await loadAliases(row)
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

async function patchRow(row, patch) {
  if (!row?.id || !props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media/${encodeURIComponent(String(row.id))}`
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

const newSubjectId = ref('')
watch(newSubjectId, async (v) => {
  if ((v === '' || v === undefined) || !props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/social-media`
    const payload = { subject_id: v === null ? null : v }
    const resp = await fetch(url, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!resp.ok) console.error('Failed to create social media row')
  } catch (e) {
    console.error(e)
  } finally {
    await load()
    newSubjectId.value = ''
  }
})
</script>

<template>
  <div class="p-2 flex flex-column gap-1">
    <div v-if="error" class="p-error mb-2">{{ error }}</div>

    <div v-if="loading" class="p-2 text-600">Loading...</div>

    <template v-for="(data, idx) in rows" :key="data.id">
      <div class="surface-card border-round p-1">
        <div class="flex flex-column gap-1">
          <div class="flex flex-wrap align-items-center gap-1">
            <span class="subject-title text-base font-bold" :style="data.rule_out ? 'text-decoration: line-through;' : ''">
              {{ data.subject?.first_name || 'Unknown' }}
              <template v-if="data.subject?.last_name"> {{ data.subject.last_name }}</template>
            </span>
          </div>

          <div class="flex flex-wrap gap-1">
            <!-- Left 8-wide cell: inputs -->
            <div class="w-12 md:w-8">
              <div class="form-grid">
                <!-- Row 1: Platform | URL -->
                <div class="field w-12 md:w-4">
                  <template v-if="data.rule_out">
                    <label class="block text-sm text-600">Platform</label>
                    <div :style="'text-decoration: line-through;'">{{ data.platform_name || data.platform_other || '—' }}</div>
                  </template>
                  <template v-else>
                    <FloatLabel variant="on">
                      <RefSelect
                        code="SM_PLATFORM"
                        v-model="data.platform_id"
                        :currentCode="data.platform_code || ''"
                        :otherValue="data.platform_other || ''"
                        @update:otherValue="(v) => { data.platform_other = v }"
                        @otherCommit="(v) => patchRow(data, { platform_other: v || null })"
                        @change="(v) => patchRow(data, { platform_id: v })"
                      />
                      <label>Platform</label>
                    </FloatLabel>
                  </template>
                </div>

                <div class="field w-12 md:w-7">
                  <template v-if="data.rule_out">
                    <label class="block text-sm text-600">URL</label>
                    <div class="flex align-items-center gap-2" :style="'text-decoration: line-through;'">{{ data.url || '—' }}</div>
                  </template>
                  <template v-else>
                    <div class="flex align-items-center gap-2">
                      <FloatLabel variant="on" class="flex-1">
                        <InputText v-model="data.url" class="w-full" @change="() => patchRow(data, { url: data.url || null })" />
                        <label>URL</label>
                      </FloatLabel>
                      <a v-if="href(data.url)" :href="href(data.url)" target="_blank" rel="noopener" title="Open">
                        <span class="material-symbols-outlined">open_in_new</span>
                      </a>
                    </div>
                  </template>
                </div>

                <!-- Row 2: Status | Investigated + Rule Out (inline) -->
                <div class="field w-12 md:w-4">
                  <template v-if="data.rule_out">
                    <label class="block text-sm text-600">Status</label>
                    <div :style="'text-decoration: line-through;'">{{ data.status_name || '—' }}</div>
                  </template>
                  <template v-else>
                    <FloatLabel variant="on">
                      <RefSelect code="SM_STAT" v-model="data.status_id" :currentCode="data.status_code || ''" @change="(v) => patchRow(data, { status_id: v })" />
                      <label>Status</label>
                    </FloatLabel>
                  </template>
                </div>

                <div class="field w-12 md:w-6">
                  <div class="flex align-items-end gap-2">
                    <div class="flex-1">
                      <template v-if="data.rule_out">
                        <label class="block text-sm text-600">Investigated</label>
                        <div :style="'text-decoration: line-through;'">{{ data.investigated_name || '—' }}</div>
                      </template>
                      <template v-else>
                        <FloatLabel variant="on" class="w-full">
                          <RefSelect code="SM_INV" v-model="data.investigated_id" :currentCode="data.investigated_code || ''" @change="(v) => patchRow(data, { investigated_id: v })" />
                          <label>Investigated</label>
                        </FloatLabel>
                      </template>
                    </div>
                    <div class="flex align-items-center gap-2 nowrap">
                      <label class="text-sm text-600">Rule Out</label>
                      <ToggleSwitch v-model="data.rule_out" @update:modelValue="(v) => patchRow(data, { rule_out: v })" />
                    </div>
                  </div>
                </div>

                <!-- Notes full width -->
                <div class="field w-11">
                  <template v-if="data.rule_out">
                    <label class="block text-sm text-600">Notes</label>
                    <div :style="'text-decoration: line-through;'">{{ data.notes || '—' }}</div>
                  </template>
                  <template v-else>
                    <FloatLabel variant="on" class="w-full">
                      <Textarea v-model="data.notes" autoResize rows="2" class="w-full" @change="() => patchRow(data, { notes: data.notes || null })" />
                      <label>Notes</label>
                    </FloatLabel>
                  </template>
                </div>
              </div>
            </div>

            <!-- Right 4-wide cell: social media aliases -->
            <div class="w-12 md:w-3">
              <div class="flex flex-column gap-1 p-1 border-1 surface-border border-round">
                <div class="text-sm text-600">Aliases</div>
                <div v-if="data._aliasesLoading" class="text-600 text-sm">Loading aliases...</div>
                <template v-for="alias in data.aliases" :key="alias.id">
                  <div class="flex flex-column gap-1 mb-1">
                    <FloatLabel variant="on">
                      <RefSelect
                        code="SM_ALIAS"
                        v-model="alias.alias_status_id"
                        :currentCode="alias.alias_status_code || ''"
                        @change="(v) => patchAlias(data, alias, { alias_status_id: v })"
                      />
                      <label>Status</label>
                    </FloatLabel>
                    <FloatLabel variant="on">
                      <InputText v-model="alias.alias" class="w-full" @change="() => patchAlias(data, alias, { alias: alias.alias || null })" />
                      <label>Alias</label>
                    </FloatLabel>
                    <div>
                      <PersonSelect v-model="alias.alias_owner_id" @change="(v) => patchAlias(data, alias, { alias_owner_id: v })" />
                    </div>
                  </div>
                </template>
                <div class="flex justify-content-end">
                  <Button label="Add Alias" size="small" icon="pi pi-plus" text @click="addAlias(data)" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Divider v-if="idx < rows.length - 1" class="my-1" />
    </template>

    <div class="mt-2 flex align-items-center gap-2">
      <span class="text-600">Add for subject:</span>
      <CasePersonSelect v-model="newSubjectId" :caseId="caseId" :primarySubject="primarySubject" />
    </div>
  </div>
</template>

<style scoped>
.form-grid { display: flex; flex-wrap: wrap; gap: 0.25rem 0.5rem; }
.field { min-width: 12rem; }
:deep(.p-divider) { margin: 0.25rem 0; }
@media (max-width: 640px) { .field { min-width: 100%; } }
</style>
