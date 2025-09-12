<script setup>
import { ref, watch, computed, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Badge from 'primevue/badge'
import api from '../../../lib/api'

// Async edit component
const SubjectsEdit = defineAsyncComponent(() => import('./SubjectsEdit.vue'))


const props = defineProps({
  caseId: { type: [String, Number], default: '' },
})

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const rows = ref([])

// set default subtab route if missing
watch(
  () => route.fullPath,
  () => {
    // Do not auto-redirect while in edit deep-link
    if (route.params.rawSubjectId) return
    const caseNumber = String(route.params.caseNumber || '')
    const sub = String(route.params.subtab || '')
    if (!sub || sub === 'contacts') {
      router.replace({ name: 'case-detail', params: { caseNumber, tab: 'contacts', subtab: 'subjects' } })
    }
  },
  { immediate: true }
)

function personName(row) {
  const s = row?.subject || {}
  return [s.first_name, s.last_name].filter(Boolean).join(' ') || 'Unknown'
}

function telHref(val) {
  if (!val) return ''
  const digits = String(val).trim().replace(/[^+\d]/g, '')
  return `tel:${digits}`
}

function relationshipDisplay(row) {
  const other = String(row?.relationship_other || '').trim()
  if (other) return other
  return row?.relationship_name || '—'
}


function phoneFor(row) {
  // Prefer nested subject.phone, but allow row-level phone fallback
  return row?.subject?.phone || row?.phone || ''
}

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/subjects`
    const resp = await api.get(url)
    rows.value = resp?.data || []
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load investigatory subjects.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

// When leaving edit mode (rawSubjectId removed), reload list
watch(
  () => route.params.rawSubjectId,
  (val, oldVal) => {
    if (oldVal && !val) {
      load()
    }
  }
)

const caseNumber = computed(() => String(route.params.caseNumber || ''))


function openEdit(row) {
  const raw = row.raw_id
  if (!raw) return
  const url = `/cases/${encodeURIComponent(String(caseNumber.value))}/contacts/subjects/${encodeURIComponent(String(raw))}`
  console.log(url);
  router.push({ path: url })
}
</script>

<template>
  <div class="p-2 flex flex-column gap-1">
    <template v-if="route.params.rawSubjectId">
      <SubjectsEdit :caseId="String(caseId)" />
    </template>
    <template v-else>
      <div v-if="error" class="p-error mb-2">{{ error }}</div>
      <DataTable :value="rows" dataKey="id" size="small" class="w-full" :loading="loading">
        <Column header="Person">
          <template #body="{ data }">
            <div class="flex align-items-center gap-2" :style="data.rule_out ? 'text-decoration: line-through;' : ''">
              <img :src="data.subject.photo_url" class="pfp-sm" alt="pfp" />
              <span>{{ personName(data) }}</span>
            </div>
          </template>
        </Column>
        <Column header="Phone">
          <template #body="{ data }">
            <template v-if="phoneFor(data)">
              <span class="icon">📞</span>
              <a :href="telHref(phoneFor(data))" class="link-btn" :style="data.rule_out ? 'text-decoration: line-through;' : ''" @click.stop>
                {{ phoneFor(data) }}
              </a>
            </template>
            <span v-else class="text-600">—</span>
          </template>
        </Column>
        <Column header="Relationship">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ relationshipDisplay(data) }}</span>
          </template>
        </Column>
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <template v-if="data?.subject?.dangerous">
              <Badge :value="data?.subject?.danger || 'Dangerous'" severity="danger" />
            </template>
          </template>
        </Column>
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" text rounded @click.stop="openEdit(data)" />
          </template>
        </Column>
      </DataTable>
      <div class="flex justify-content-start mt-2">
        <Button label="Add" icon="pi pi-plus" @click="() => router.push({ path: `/cases/${encodeURIComponent(String(caseNumber))}/contacts/subjects/new` })" />
      </div>
    </template>
  </div>
</template>

<style scoped>
.pfp-sm { width: 32px; height: 32px; border-radius: 999px; object-fit: cover; }
</style>
