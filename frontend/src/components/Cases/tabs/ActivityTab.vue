<script setup>
import { ref, watch, computed, defineAsyncComponent } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Badge from 'primevue/badge'
import api from '../../../lib/api'

const ActivityEdit = defineAsyncComponent(() => import('./ActivityEdit.vue'))

const props = defineProps({
  caseId: { type: [String, Number], default: '' },
})

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const error = ref('')
const rows = ref([])

async function load() {
  if (!props.caseId) { rows.value = []; return }
  loading.value = true
  error.value = ''
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/activity`
    const resp = await api.get(url)
    rows.value = resp?.data || []
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load activity.'
    rows.value = []
  } finally {
    loading.value = false
  }
}

watch(() => props.caseId, () => { load() }, { immediate: true })

const caseNumber = computed(() => String(route.params.caseNumber || ''))

function openEdit(row) {
  const id = row?.id
  if (!id) return
  const url = `/cases/${encodeURIComponent(String(caseNumber.value))}/activity/${encodeURIComponent(String(id))}`
  router.push({ path: url })
}

// When leaving edit mode (subtab removed), reload list
watch(
  () => route.params.subtab,
  (val, oldVal) => {
    if (oldVal && !val) {
      load()
    }
  }
)

async function addRow() {
  if (!props.caseId) return
  try {
    const url = `/api/v1/cases/${encodeURIComponent(String(props.caseId))}/activity`
    await api.post(url, {})
  } catch (e) {
    console.error(e)
  } finally {
    await load()
  }
}
</script>

<template>
  <div class="p-2 flex flex-column gap-1">
    <template v-if="route.params.subtab">
      <ActivityEdit :caseId="String(caseId)" />
    </template>
    <template v-else>
      <div v-if="error" class="p-error mb-2">{{ error }}</div>
      <DataTable :value="rows" dataKey="id" size="small" class="w-full" :loading="loading">
        <Column header="Date" field="date" />
        <Column header="What">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.what || '—' }}</span>
          </template>
        </Column>
        <Column header="Source">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.source_name || data.source_other || '—' }}</span>
          </template>
        </Column>
        <Column header="Reported To">
          <template #body="{ data }">
            <span :style="data.rule_out ? 'text-decoration: line-through;' : ''">{{ data.reported_to_name || data.reported_to_other || '—' }}</span>
          </template>
        </Column>
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <template v-if="data.on_eod_report">
              <Badge value="EOD" severity="info" />
            </template>
          </template>
        </Column>
        <Column header="" style="width:1%">
          <template #body="{ data }">
            <template v-if="data.rule_out">
              <Badge value="Rule Out" severity="warning" />
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
        <Button label="Add" icon="pi pi-plus" @click="addRow" />
      </div>
    </template>
  </div>
</template>

<style scoped>
</style>
