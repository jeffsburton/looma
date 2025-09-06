<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import FileUpload from 'primevue/fileupload'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import FloatLabel from 'primevue/floatlabel'
import Toast from 'primevue/toast'
import Badge from 'primevue/badge'
import Message from 'primevue/message'
import api from '@/lib/api'
import { useToast } from 'primevue/usetoast'

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
  caseId: { type: [String, Number], required: false }
})

const items = ref([])
const loading = ref(false)

const showDialog = ref(false)
const editing = ref(null)
const saving = ref(false)

const totalSize = ref(0)
const amountCompleted = ref(0)
const totalSizePercent = ref(0)

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  let i = Math.floor(Math.log(bytes) / Math.log(k))
  i = Math.min(i, sizes.length - 1)
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

function isVideoType(type) {
  const t = (type || '').toLowerCase()
  return t.startsWith('video/')
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

function onClearUpload() {
  totalSize.value = 0
  amountCompleted.value = 0
  totalSizePercent.value = 0
}

function onRemoveFile(file, removeFileCallback, index) {
  removeFileCallback(index)
  totalSize.value -= file.size
}

function onSelectedFiles(event, files, uploadedFiles) {
  const selected = event.files || []
  const keep = []
  for (const f of selected) {
    if (isVideoType(f.type)) {
      try { toast.add({ severity: 'warn', summary: 'Rejected', detail: `${f.name}: videos are not allowed here.`, life: 4000 }) } catch(_) {}
    } else {
      keep.push(f)
    }
  }
  // Replace event files with filtered
  event.files.length = 0
  keep.forEach(f => event.files.push(f))

  // Update counters
  totalSize.value = (files || []).reduce((acc, f) => acc + (f.size || 0), 0)
}

async function onUploadFiles(files, uploadedFiles) {
  if (!props.caseId) return
  const filesToProcess = [...files]

  for (const file of filesToProcess) {
    try {
      const fd = new FormData()
      fd.append('file', file, file.name)
      await api.post(`/api/v1/cases/${casePathId(props.caseId)}/files/upload`, fd, {
        onUploadProgress: (evt) => {
          const loaded = evt.loaded || 0
          const filePercent = Math.min(100, (loaded / file.size) * 100)
          const previouslyCompleted = amountCompleted.value - (amountCompleted._filePartial || 0)
          amountCompleted._filePartial = loaded
          const overall = previouslyCompleted + loaded
          totalSizePercent.value = Math.min(100, (overall / (totalSize.value || 1)) * 100)
        }
      })

      const prevPartial = amountCompleted._filePartial || 0
      amountCompleted.value += (file.size - prevPartial)
      amountCompleted._filePartial = 0
      totalSizePercent.value = Math.min(100, (amountCompleted.value / (totalSize.value || 1)) * 100)

      toast.add({ severity: 'success', summary: 'Uploaded', detail: file.name, life: 2500 })
      const index = files.findIndex(f => f === file)
      if (index > -1) files.splice(index, 1)
    } catch (e) {
      console.error(e)
      toast.add({ severity: 'error', summary: 'Upload failed', detail: `${file.name}: ${e?.message || e}`, life: 5000 })
    }
  }

  totalSizePercent.value = 0
  await loadFiles()
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
const pastedFiles = ref([])
const showingPastePrompt = ref(false)

async function fileFromClipboardItem(item) {
  const blob = item.getAsFile ? item.getAsFile() : null
  if (!blob) throw new Error('Clipboard item has no file')
  const type = blob.type || 'image/png'
  const ext = type.includes('png') ? 'png' : type.includes('jpeg') ? 'jpg' : type.includes('gif') ? 'gif' : 'png'
  const name = `pasted-${new Date().toISOString().replace(/[:.]/g, '-')}.${ext}`
  return new File([blob], name, { type, lastModified: Date.now() })
}

async function onPaste(e) {
  try {
    const dt = e.clipboardData || window.clipboardData
    if (!dt) return
    const itemsArr = Array.from(dt.items || [])
    const imageItems = itemsArr.filter(i => i.type && i.type.startsWith('image/'))
    if (!imageItems.length) return

    const newlyQueued = []
    for (const it of imageItems) {
      const file = await fileFromClipboardItem(it)
      if (!file.type.startsWith('image/')) continue
      if (isVideoType(file.type)) continue // just in case
      if (file.size > 1000000000) continue
      newlyQueued.push(file)
    }

    if (!newlyQueued.length) return

    for (const f of newlyQueued) totalSize.value += f.size

    pastedFiles.value.push(...newlyQueued)
    showingPastePrompt.value = true
    try { toast.add({ severity: 'info', summary: 'Paste detected', detail: `Added ${newlyQueued.length} file(s) from clipboard. Click Upload to proceed.`, life: 3500 }) } catch (_) {}
  } catch (err) {
    console.error(err)
    try { toast.add({ severity: 'error', summary: 'Paste failed', detail: String(err?.message || err), life: 4000 }) } catch (_) {}
  }
}

async function uploadPasted() {
  if (!pastedFiles.value.length) return
  await onUploadFiles([...pastedFiles.value], [])
  pastedFiles.value.splice(0)
  showingPastePrompt.value = false
}

function discardPasted() {
  if (!pastedFiles.value.length) { showingPastePrompt.value = false; return }
  for (const f of pastedFiles.value) {
    totalSize.value -= f.size
  }
  if (totalSize.value < 0) totalSize.value = 0
  totalSizePercent.value = totalSize.value ? 100 * (amountCompleted.value / totalSize.value) : 0
  pastedFiles.value.splice(0)
  showingPastePrompt.value = false
}

function removePastedFile(file) {
  try { totalSize.value -= file?.size || 0 } catch {}
  if (totalSize.value < 0) totalSize.value = 0
  const idx = pastedFiles.value.indexOf(file)
  if (idx > -1) pastedFiles.value.splice(idx, 1)
  if (!pastedFiles.value.length) showingPastePrompt.value = false
}

</script>
<template>
  <div class="p-3" @paste.prevent="onPaste">
    <Toast />

    <div v-if="showingPastePrompt" class="flex items-center gap-2 mb-2">
      <Message severity="info">Pasted image(s) ready to upload.</Message>
      <Button icon="pi pi-cloud-upload" label="Upload now" @click="uploadPasted" />
      <Button icon="pi pi-times" label="Discard" severity="danger" variant="outlined" @click="discardPasted" />
    </div>

    <div v-if="pastedFiles.length > 0" class="w-full mb-3">
      <div v-for="(file, index) in pastedFiles" :key="file.name + file.type + file.size" class="w-full space-y-1">
        <div class="flex items-center gap-2">
          <i class="pi text-2xl" :class="extensionIcon(file.name)"></i>
          <div class="flex-1 min-w-0">
            <span class="font-semibold text-ellipsis whitespace-nowrap overflow-hidden block">{{ file.name }}</span>
            <div class="text-sm text-gray-600">{{ formatSize(file.size) }}</div>
          </div>
          <div class="shrink-0">
            <Badge value="Pending" severity="warn" />
          </div>
          <div class="shrink-0">
            <Button icon="pi pi-times" @click="removePastedFile(file)" variant="outlined" rounded severity="danger" size="small" />
          </div>
        </div>
      </div>
    </div>

    <div class="flex align-items-center gap-3 mb-3 wrap">
      <div class="w-full">
        <FileUpload name="other[]"
                    :multiple="true"
                    :auto="false"
                    :maxFileSize="1000000000"
                    @select="onSelectedFiles($event, files, uploadedFiles)"
                    @clear="onClearUpload($event)">
          <template #header="{ chooseCallback, uploadCallback, clearCallback, files, uploadedFiles }">
            <div class="flex flex-wrap justify-between items-center flex-1 gap-4">
              <div class="flex gap-2">
                <Button @click="chooseCallback()" class="file-upload-buttons"><i class="pi pi-plus"></i> Choose</Button>
                <Button @click="onUploadFiles(files, uploadedFiles)" class="file-upload-buttons" severity="secondary" :disabled="!files || files.length === 0"><i class="pi pi-cloud-upload"></i> Upload</Button>
                <Button @click="clearCallback()" class="file-upload-buttons" severity="secondary" :disabled="!files || files.length === 0"><i class="pi pi-times"></i> Clear</Button>
              </div>
              <ProgressBar :value="totalSizePercent" :showValue="false" class="md:w-20rem h-1 w-full md:ml-auto">
                <span class="whitespace-nowrap">{{ totalSize }}B</span>
              </ProgressBar>
            </div>
          </template>
          <template #content="{ files, uploadedFiles, removeFileCallback, messages }">
            <Message v-for="message of messages" :key="message" :class="{ 'mb-8': !files.length && !uploadedFiles.length}" severity="error">
              {{ message }}
            </Message>
            <div class="w-full">
              <div v-if="files.length > 0">
                <div v-for="(file, index) of files" :key="file.name + file.type + file.size" class="w-full space-y-1">
                  <div class="flex items-center gap-2">
                    <i class="pi text-2xl" :class="extensionIcon(file.name)"></i>
                    <div class="flex-1 min-w-0">
                      <span class="font-semibold text-ellipsis whitespace-nowrap overflow-hidden block">{{ file.name }}</span>
                      <div class="text-sm text-gray-600">{{ formatSize(file.size) }}</div>
                    </div>
                    <div class="shrink-0">
                      <Badge value="Pending" severity="warn" />
                    </div>
                    <div class="shrink-0">
                      <Button icon="pi pi-times" @click="onRemoveFile(file, removeFileCallback, index)" variant="outlined" rounded severity="danger" size="small" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
          <template #empty>
            <div class="flex items-center justify-center flex-col">
              <p class="mt-1 mb-0">Drag and drop files here to upload (videos not allowed). <strong>Photos of people, places & things belong in Photos. Only images of documents should be uploaded here. </strong></p>
            </div>
          </template>
        </FileUpload>
      </div>
    </div>

    <div class="mb-2 text-900 font-medium">Files</div>
    <DataTable :value="items" dataKey="id" :loading="loading" v-if="hasItems">
      <Column header="Type" style="width: 60px">
        <template #body="{ data }">
          <i class="pi text-2xl" :class="extensionIcon(data.file_name)"></i>
        </template>
      </Column>
      <Column field="file_name" header="Name" />
      <Column header="Source">
        <template #body="{ data }">{{ data.source || '—' }}</template>
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
