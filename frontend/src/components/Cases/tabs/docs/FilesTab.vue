<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from 'vue'
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
import CaseSubjectSelect from '@/components/cases/CaseSubjectSelect.vue'
import SubjectPanel from '@/components/contacts/Subject.vue'

// Helpers to avoid double-encoding and to prefer numeric case id when present (e.g., "2.xyz==" -> "2")
function safeEncode(id) {
  const s = String(id ?? '')
  if (/%[0-9a-fA-F]{2}/.test(s)) return s
  try { return encodeURIComponent(s) } catch { return s }
}
function casePathId(id) {
  const s = String(id ?? '')
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

// File subjects management (copied from ImagesTab, adapted for files)
const fileSubjects = ref([])
const subjectsLoading = ref(false)
const newSubjectId = ref('')

// Subject detail dialog
const subjectDialogVisible = ref(false)
const subjectModel = ref(null)
const subjectLoading = ref(false)

async function openSubject(opaqueId) {
  if (!opaqueId) return
  subjectLoading.value = true
  try {
    const { data } = await api.get(`/api/v1/subjects`, { headers: { 'Accept': 'application/json' } })
    const arr = Array.isArray(data) ? data : []
    const subj = arr.find(s => s?.id === opaqueId)
    if (!subj) {
      try { toast.add({ severity: 'warn', summary: 'Not found', detail: 'Subject not found.', life: 2500 }) } catch (_) {}
      return
    }
    subjectModel.value = {
      id: subj.id,
      first_name: subj.first_name || '',
      last_name: subj.last_name || '',
      phone: subj.phone || '',
      email: subj.email || '',
      dangerous: !!subj.dangerous,
      danger: subj.danger || '',
    }
    subjectDialogVisible.value = true
  } catch (e) {
    console.error(e)
    try { toast.add({ severity: 'error', summary: 'Error', detail: 'Failed to load subject details.', life: 3000 }) } catch (_) {}
  } finally {
    subjectLoading.value = false
  }
}

async function loadFileSubjects() {
  if (!props.caseId || !editing.value?.id) return
  subjectsLoading.value = true
  try {
    const { data } = await api.get(`/api/v1/cases/${casePathId(props.caseId)}/files/${encodeURIComponent(editing.value.id)}/subjects`)
    fileSubjects.value = Array.isArray(data) ? data : []
  } catch (e) {
    fileSubjects.value = []
  } finally {
    subjectsLoading.value = false
  }
}

async function addFileSubject(subjectId) {
  const sid = subjectId || newSubjectId.value
  if (!props.caseId || !editing.value?.id || !sid) return
  try {
    await api.post(
      `/api/v1/cases/${casePathId(props.caseId)}/files/${encodeURIComponent(editing.value.id)}/subjects`,
      { subject_id: sid },
      { headers: { 'Accept': 'application/json' } }
    )
    newSubjectId.value = ''
    await loadFileSubjects()
  } catch (e) {
    console.error(e)
  }
}

function onSelectNewSubject(v) {
  if (!v) return
  const alreadyLinked = fileSubjects.value?.some(s => s.subject_id === v)
  if (alreadyLinked) {
    try { toast.add({ severity: 'info', summary: 'Already added', detail: 'This subject is already linked to the file.', life: 2500 }) } catch (_) {}
    newSubjectId.value = ''
    return
  }
  addFileSubject(v)
}

async function deleteFileSubject(linkId) {
  if (!props.caseId || !editing.value?.id || !linkId) return
  try {
    await api.delete(`/api/v1/cases/${casePathId(props.caseId)}/files/${encodeURIComponent(editing.value.id)}/subjects/${encodeURIComponent(linkId)}`)
    fileSubjects.value = fileSubjects.value.filter(s => s.id !== linkId)
  } catch (e) {
    console.error(e)
  }
}


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
  // Load file-subject links for this file
  loadFileSubjects()
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

// Lightbox state and helpers (mirrors ImagesTab behavior)
const showLightbox = ref(false)
const lightboxItem = ref(null)

function openLightbox(item) {
  if (!item) return
  lightboxItem.value = item
  showLightbox.value = true
}
function closeLightbox() {
  showLightbox.value = false
  lightboxItem.value = null
}
function isVideo(item) {
  const mt = item?.mime_type || ''
  return typeof mt === 'string' && mt.toLowerCase().startsWith('video')
}

// Close lightbox on Escape key
function onKeydown(e) {
  if (!showLightbox.value) return
  const key = e?.key || e?.code || ''
  if (key === 'Escape' || key === 'Esc') {
    e.preventDefault()
    closeLightbox()
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
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
            <img
              :src="data.thumb"
              alt="thumb"
              style="width:40px;height:40px;object-fit:cover;border-radius:4px;cursor:pointer;"
              role="button"
              @click="openLightbox(data)"
            />
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

      <!-- Subjects list and add (copied from ImagesTab, adapted) -->
      <div class="field mt-3">
        <div class="label mb-2">Subjects in File</div>
        <div v-if="subjectsLoading" class="text-600 text-sm mb-2">Loading…</div>
        <ul v-else class="subject-list">
          <li v-for="s in fileSubjects" :key="s.id" class="subject-row">
            <div class="subject-info clickable" @click.stop="openSubject(s.subject_id)">
              <img :src="s.photo_url" :alt="s.name" class="subject-avatar" />
              <span class="subject-name">{{ s.name }}</span>
            </div>
            <Button icon="pi pi-trash" text size="small" @click="deleteFileSubject(s.id)" />
          </li>
          <li v-if="fileSubjects.length === 0" class="text-600 text-sm">No subjects linked.</li>
        </ul>
        <div class="mt-2">
          <FloatLabel variant="on">
            <CaseSubjectSelect
              v-model="newSubjectId"
              :caseId="String(props.caseId || '')"
              :filter="true"
              :includeUnknown="false"
              class="w-full"
              @change="onSelectNewSubject"
            />
            <label>Add Subject</label>
          </FloatLabel>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <Button label="Cancel" severity="secondary" @click="showDialog=false" />
          <Button label="Save" :loading="saving" @click="saveEdit" />
        </div>
      </template>
    </Dialog>

    <!-- Subject Dialog -->
    <Dialog v-model:visible="subjectDialogVisible" modal header="Subject" :style="{ width: '640px' }">
      <div v-if="subjectLoading" class="p-3 text-600">Loading…</div>
      <SubjectPanel v-else-if="subjectModel" v-model="subjectModel" :isNew="false" :canModify="true" @updated="() => {}" @avatarChanged="() => {}" />
      <template #footer>
        <Button label="Close" text @click="subjectDialogVisible=false" />
      </template>
    </Dialog>

    <!-- Lightbox Overlay (images/videos) -->
    <div v-if="showLightbox" class="lightbox" @click.self="closeLightbox">
      <button class="lightbox-close" type="button" @click="closeLightbox" aria-label="Close">
        <i class="pi pi-times"></i>
      </button>
      <div class="lightbox-center">
        <div class="lightbox-content">
          <template v-if="lightboxItem">
            <video v-if="isVideo(lightboxItem)" :src="lightboxItem.url" controls class="lightbox-media"></video>
            <img v-else :src="lightboxItem.url" alt="preview" class="lightbox-media" />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lightbox { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 1000; }
.lightbox-close { position: fixed; top: 12px; right: 12px; width: 40px; height: 40px; border-radius: 50%; border: 1px solid rgba(255,255,255,0.4); background: rgba(0,0,0,0.4); color: #fff; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; z-index: 1001; }
.lightbox-close .pi { font-size: 18px; }
.lightbox-center { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; padding: 2vw; }
.lightbox-content { max-width: 80vw; max-height: 90vh; background: transparent; display: flex; align-items: center; justify-content: center; }
.lightbox-media { max-width: 80vw; max-height: 90vh; object-fit: contain; display: block; }
.subject-list { list-style: none; padding: 0; margin: 0; }
.subject-row { display: flex; align-items: center; justify-content: space-between; padding: .25rem 0; border-bottom: 1px solid var(--p-surface-200); }
.subject-row:last-child { border-bottom: 0; }
.subject-info { display: flex; align-items: center; gap: .5rem; min-width: 0; flex: 1 1 auto; }
.subject-avatar { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.subject-name { flex: 1 1 auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
