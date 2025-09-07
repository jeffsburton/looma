<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Toast from 'primevue/toast'
import SelectButton from 'primevue/selectbutton'
import api from '@/lib/api'
import { useToast } from 'primevue/usetoast'
import FileUpload from '@/components/common/FileUpload.vue'

// Helpers to avoid double-encoding and to prefer numeric case id when present (e.g., "2.xyz==" -> "2")
function safeEncode(id) {
  const s = String(id ?? '')
  if (/%[0-9a-fA-F]{2}/.test(s)) return s
  try { return encodeURIComponent(s) } catch { return s }
}
function casePathId(id) {
  const s = String(id ?? '')
  const m = s.match(/^(\d+)/)
  if (m && m[1]) return m[1]
  return safeEncode(s)
}

const toast = useToast()

const props = defineProps({
  caseId: { type: [String], required: true }
})

const items = ref([])
const loading = ref(false)

// Toolbar state: search and type filters
const searchQuery = ref('')
const typeOptions = [
  { label: 'Photos', value: 'photos', icon: 'pi pi-image' },
  { label: 'Video', value: 'video', icon: 'pi pi-video' },
  { label: 'Documents', value: 'documents', icon: 'pi pi-file' },
]
const selectedTypes = ref(typeOptions.map(o => o.value)) // multiple selection (default: all selected)

const showDialog = ref(false)
const editing = ref(null)
const saving = ref(false)


function extensionIcon(name) {
  const n = String(name || '').toLowerCase()
  if (n.endsWith('.pdf')) return 'pi-file-pdf'
  if (/(\.doc|\.docx|\.docm|\.dot|\.dotx)$/.test(n)) return 'pi-file-word'
  if (/(\.xls|\.xlsx|\.xlsm|\.xlt|\.xltx)$/.test(n)) return 'pi-file-excel'
  if (/(\.png|\.jpg|\.jpeg|\.gif|\.bmp|\.webp|\.tif|\.tiff|\.svg)$/.test(n)) return 'pi-image'
  return 'pi-file'
}

async function loadFiles() {
  if (!props.caseId) return
  loading.value = true
  try {
    const { data } = await api.get(`/api/v1/cases/${casePathId(props.caseId)}/files`)
    items.value = Array.isArray(data) ? data : []
  } catch (e) {
    items.value = []
  } finally {
    loading.value = false
  }
}


function downloadItem(item) {
  try {
    const href = item?.url
    if (!href) return
    const a = document.createElement('a')
    a.href = href
    a.download = item?.file_name || 'download'
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
  } catch (e) {
    try { window.open(item?.url, '_blank', 'noopener') } catch (_) {}
  }
}

function openEdit(item) {
  editing.value = { ...item }
  showDialog.value = true
}

async function saveEdit() {
  if (!props.caseId || !editing.value) return
  saving.value = true
  try {
    const payload = {
      source: editing.value.source ?? null,
      where: editing.value.where ?? null,
      notes: editing.value.notes ?? null,
    }
    const { data } = await api.patch(`/api/v1/cases/${casePathId(props.caseId)}/files/${encodeURIComponent(editing.value.id)}`, payload)
    // Merge back into list
    const idx = items.value.findIndex(x => x.id === editing.value.id)
    if (idx > -1) items.value[idx] = data
    showDialog.value = false
    editing.value = null
    toast.add({ severity: 'success', summary: 'Saved', life: 2000 })
  } catch (e) {
    console.error(e)
    toast.add({ severity: 'error', summary: 'Save failed', detail: e?.message || 'Error', life: 4000 })
  } finally {
    saving.value = false
  }
}

onMounted(loadFiles)

watch(() => props.caseId, () => { loadFiles() })


const hasItems = computed(() => (items.value || []).length > 0)

// Filtered items based on search and type selections
const filteredItems = computed(() => {
  const q = (searchQuery.value || '').trim().toLowerCase()
  const types = Array.isArray(selectedTypes.value) ? selectedTypes.value : []
  const applyType = (it) => {
    if (!types.length) return true
    let ok = false
    for (const t of types) {
      if (t === 'photos' && it.is_image === true && it.is_document === false) ok = true
      if (t === 'video' && it.is_video === true) ok = true
      if (t === 'documents' && it.is_document === true) ok = true
      if (ok) break
    }
    return ok
  }
  const applySearch = (it) => {
    if (!q) return true
    const fields = [it.file_name, it.source, it.where, it.notes, it.created_by_name]
    return fields.some(v => String(v || '').toLowerCase().includes(q))
  }
  return (items.value || []).filter(it => applyType(it) && applySearch(it))
})


</script>
<template>
  <div class="p-3">
    <Toast />

    <FileUpload :caseId="caseId" @uploaded="loadFiles" />

    <!-- Toolbar: Search + Type Filters -->
    <div class="flex flex-wrap items-center gap-3 mb-3">
      <div class="flex-1 min-w-[220px]">
        <FloatLabel variant="on" class="w-full">
          <InputText id="file-search" v-model="searchQuery" class="w-full" placeholder="Search" />
          <label for="file-search">Search</label>
        </FloatLabel>
      </div>
      <div class="min-w-[220px]">
        <FloatLabel variant="on" class="w-full">
          <SelectButton id="type-filter" v-model="selectedTypes" :options="typeOptions" optionLabel="label" optionValue="value" :multiple="true">
            <template #option="slotProps">
              <i :class="slotProps.option.icon" class="mr-2"></i>
            </template>
          </SelectButton>
        </FloatLabel>
      </div>
    </div>

    <DataTable :value="filteredItems" dataKey="id" :loading="loading" v-if="hasItems">
      <Column header="Type" style="width: 60px">
        <template #body="{ data }">
          <template v-if="(data.is_image || data.is_video) && data.thumb">
            <img :src="data.thumb" alt="thumb" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />
          </template>
          <template v-else>
            <i class="pi text-2xl" :class="extensionIcon(data.file_name)"></i>
          </template>
        </template>
      </Column>
      <Column field="file_name" header="Name" />
      <Column header="Source">
        <template #body="{ data }">{{ data.source || '—' }}</template>
      </Column>
      <Column header="Where">
        <template #body="{ data }">{{ data.where || '—' }}</template>
      </Column>
      <Column header="Notes">
        <template #body="{ data }">{{ data.notes || '—' }}</template>
      </Column>
      <Column header="Actions" style="width: 140px">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button icon="pi pi-download" size="small" @click="downloadItem(data)" v-tooltip.top="'Download'" />
            <Button icon="pi pi-pencil" size="small" @click="openEdit(data)" severity="secondary" v-tooltip.top="'Edit'" />
          </div>
        </template>
      </Column>
    </DataTable>
    <div v-else class="text-600">No files uploaded yet.</div>

    <Dialog v-model:visible="showDialog" modal header="Edit File" :style="{ width: '600px' }">
      <div class="mt-2 gap-2">
        <FloatLabel variant="on" class="mb-2">
          <InputText id="source" v-model="editing.source" class="w-full" />
          <label for="source">Source</label>
        </FloatLabel>
        <FloatLabel variant="on" class="mb-2">
          <InputText id="where" v-model="editing.where" class="w-full" />
          <label for="where">Where</label>
        </FloatLabel>
        <FloatLabel variant="on">
          <Textarea id="notes" v-model="editing.notes" class="w-full" rows="4" />
          <label for="notes">Notes</label>
        </FloatLabel>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <Button label="Cancel" severity="secondary" @click="showDialog=false" />
          <Button label="Save" :loading="saving" @click="saveEdit" />
        </div>
      </template>
    </Dialog>
  </div>
</template>
