<script setup>
import { ref, computed } from 'vue'
import FileUpload from 'primevue/fileupload'
import Button from 'primevue/button'
import ProgressBar from 'primevue/progressbar'
import Message from 'primevue/message'
import Badge from 'primevue/badge'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import api from '@/lib/api'

const props = defineProps({
  caseId: { type: [String, Number], required: true },
  singleFile: { type: Boolean, default: false },
})

const emit = defineEmits(['uploaded'])

const totalSize = ref(0)
const amountCompleted = ref(0)
const totalSizePercent = ref(0)

const pastedFiles = ref([])
const showingPastePrompt = ref(false)

const toast = useToast()

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  let i = Math.floor(Math.log(bytes) / Math.log(k))
  i = Math.min(i, sizes.length - 1)
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

function extensionIcon(name) {
  const n = String(name || '').toLowerCase()
  if (n.endsWith('.pdf')) return 'pi-file-pdf'
  if (/(\.doc|\.docx|\.docm|\.dot|\.dotx)$/.test(n)) return 'pi-file-word'
  if (/(\.xls|\.xlsx|\.xlsm|\.xlt|\.xltx)$/.test(n)) return 'pi-file-excel'
  if (/(\.png|\.jpg|\.jpeg|\.gif|\.bmp|\.webp|\.tif|\.tiff|\.svg)$/.test(n)) return 'pi-image'
  return 'pi-file'
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

async function onSelectedFiles(event, files, uploadedFiles) {
  const selected = event.files || []
  const keep = props.singleFile ? selected.slice(0, 1) : selected.slice()
  event.files.length = 0
  keep.forEach(f => event.files.push(f))

  for (const file of event.files) {
    try {
      let blob = null
      if (file.type && file.type.startsWith('video/')) {
        blob = await extractFrameFromFile(file, 0.12, 'image/jpeg', 0.95, 200)
      } else if (file.type && file.type.startsWith('image/')) {
        blob = await createThumbnail(file)
      }
      if (blob) file.thumbBlob = blob
    } catch (e) {
      console.warn('Failed to generate thumbnail for file', file?.name, e)
    }
  }
  totalSize.value = (files || []).reduce((acc, f) => acc + (f.size || 0), 0)

  // Auto-start upload immediately after selection/drag-drop
  try {
    await onUploadFiles(event.files, uploadedFiles)
  } catch (e) {
    console.error(e)
  }
}

async function onUploadFiles(files, uploadedFiles) {
  if (!props.caseId) return
  //console.log(files);
  const filesToProcess = [...files]
  for (const file of filesToProcess) {
    try {
      const fd = new FormData()
      fd.append('file', file, file.name)
      try {
        if (file.thumbBlob) {
          fd.append('thumbnail', file.thumbBlob, 'thumbnail.jpg')
        }
      } catch (e) {
        console.warn('Thumbnail append failed:', e)
      }
      console.log(props.caseId);
      const resp = await api.post(`/api/v1/cases/${casePathId(props.caseId)}/files/upload`, fd, {
        onUploadProgress: (evt) => {
          const loaded = evt.loaded || 0
          const prev = amountCompleted._filePartial || 0
          const previouslyCompleted = amountCompleted.value - prev
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
      const uploaded = resp && resp.data ? resp.data : null
      if (uploaded) emit('uploaded', uploaded)
      const index = files.findIndex(f => f === file)
      if (index > -1) files.splice(index, 1)
    } catch (e) {
      console.error(e)
      toast.add({ severity: 'error', summary: 'Upload failed', detail: `${file.name}: ${e?.message || e}`, life: 5000 })
    }
  }
  totalSizePercent.value = 0
  emit('uploaded')
}

function casePathId(id) {
  const s = String(id ?? '')
  try { return encodeURIComponent(s) } catch { return s }
}

function extractFrameFromURL(src, timeSec = 0.1, type = 'image/jpeg', quality = 0.9, targetWidth) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video')
    video.preload = 'auto'
    video.muted = true
    video.playsInline = true
    video.crossOrigin = 'anonymous'
    video.src = src
    const fail = (msg) => reject(new Error(msg))
    video.addEventListener('error', () => fail('Failed to load video'))
    video.addEventListener('loadedmetadata', () => {
      if (!video.videoWidth || !video.videoHeight) return fail('No video dimensions')
      const t = Math.min(timeSec, Math.max(0.01, (video.duration || 1) * 0.01))
      const onSeeked = () => {
        const vw = video.videoWidth
        const vh = video.videoHeight
        let outW = vw
        let outH = vh
        if (targetWidth && targetWidth > 0) {
          outW = targetWidth
          outH = Math.round((vh / vw) * outW)
        }
        const canvas = document.createElement('canvas')
        canvas.width = outW
        canvas.height = outH
        const ctx = canvas.getContext('2d')
        ctx.drawImage(video, 0, 0, outW, outH)
        canvas.toBlob((blob) => {
          if (!blob) return fail('Canvas toBlob failed')
          resolve(blob)
        }, type, quality)
      }
      video.addEventListener('seeked', onSeeked, { once: true })
      try { video.currentTime = t } catch {
        video.addEventListener('loadeddata', () => { video.currentTime = t }, { once: true })
      }
    }, { once: true })
  })
}
async function extractFrameFromFile(file, timeSec = 0.1, type = 'image/jpeg', quality = 0.9, targetWidth) {
  const url = URL.createObjectURL(file)
  try {
    return await extractFrameFromURL(url, timeSec, type, quality, targetWidth)
  } finally {
    URL.revokeObjectURL(url)
  }
}
async function createThumbnail(file, type = 'image/jpeg', quality = 0.95, targetWidth = 200) {
  const url = URL.createObjectURL(file)
  return new Promise((resolve, reject) => {
    const img = new Image()
    img.onload = () => {
      try {
        const aspectRatio = img.height / img.width
        const targetHeight = Math.round(targetWidth * aspectRatio)
        const canvas = document.createElement('canvas')
        canvas.width = targetWidth
        canvas.height = targetHeight
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = 'white'
        ctx.fillRect(0, 0, targetWidth, targetHeight)
        ctx.drawImage(img, 0, 0, targetWidth, targetHeight)
        canvas.toBlob((blob) => {
          URL.revokeObjectURL(url)
          if (blob) resolve(blob)
          else reject(new Error('Failed to create thumbnail blob'))
        }, type, quality)
      } catch (error) {
        URL.revokeObjectURL(url)
        reject(error)
      }
    }
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Failed to load image')) }
    img.crossOrigin = 'anonymous'
    img.src = url
  })
}

async function fileFromClipboardItem(item) {
  const blob = item.getAsFile ? item.getAsFile() : null
  if (!blob) throw new Error('Clipboard item has no file')
  const type = blob.type || 'image/png'
  let ext = 'bin'
  if (type.includes('png')) ext = 'png'
  else if (type.includes('jpeg')) ext = 'jpg'
  else if (type.includes('gif')) ext = 'gif'
  else if (type.includes('mp4')) ext = 'mp4'
  else if (type.startsWith('video/')) ext = 'mp4'
  else if (type.startsWith('image/')) ext = 'jpg'
  const name = `pasted-${new Date().toISOString().replace(/[:.]/g, '-')}.${ext}`
  return new File([blob], name, { type, lastModified: Date.now() })
}

async function onPaste(e) {
  try {
    const dt = e.clipboardData || window.clipboardData
    if (!dt) return
    const itemsArr = Array.from(dt.items || [])
    const fileItems = itemsArr.filter(i => i.type && (i.type.startsWith('image/') || i.type.startsWith('video/')))
    if (!fileItems.length) return

    const newlyQueued = []
    for (const it of fileItems) {
      const file = await fileFromClipboardItem(it)
      if (file.size > 1000000000) continue
      try {
        let blob = null
        if (file.type && file.type.startsWith('video/')) {
          blob = await extractFrameFromFile(file, 0.12, 'image/jpeg', 0.95, 200)
        } else if (file.type && file.type.startsWith('image/')) {
          blob = await createThumbnail(file)
        }
        if (blob) file.thumbBlob = blob
      } catch (e) {
        console.warn('Paste thumbnail generation failed:', e)
      }
      newlyQueued.push(file)
      if (props.singleFile) break
    }

    if (!newlyQueued.length) return

    for (const f of newlyQueued) totalSize.value += f.size

    // Auto-upload pasted files immediately
    await onUploadFiles([...newlyQueued], [])
    // Reset counters for next batch
    amountCompleted.value = 0
    totalSize.value = 0
    totalSizePercent.value = 0
    try { toast.add({ severity: 'success', summary: 'Pasted upload complete', detail: `Uploaded ${newlyQueued.length} file(s).`, life: 3000 }) } catch (_) {}
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
  for (const f of pastedFiles.value) totalSize.value -= f.size
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
                    :multiple="!singleFile"
                    :auto="false"
                    :maxFileSize="1000000000"
                    @select="onSelectedFiles($event, files, uploadedFiles)"
                    @clear="onClearUpload($event)">
          <template #header="{ chooseCallback, uploadCallback, clearCallback, files, uploadedFiles }">
            <div class="flex flex-wrap justify-between items-center flex-1 gap-4">
              <div  v-if="files.length === 0" class="flex gap-2">
                <Button @click="chooseCallback()" class="file-upload-buttons"><i class="pi pi-plus"></i> Choose</Button>
               </div>
              <ProgressBar v-if="files.length > 0" :value="totalSizePercent" :showValue="false" class="md:w-20rem h-1 w-full md:ml-auto">
                <span class="whitespace-nowrap">{{ totalSize }}B</span>
              </ProgressBar>
            </div>
          </template>
          <template #content/>
          <template #empty>
            <div class="flex items-center justify-center flex-col">
              <p class="mt-1 mb-0">Drag and drop files here to upload. <strong>Photos of people, places & things belong in Photos. Only images of documents should be uploaded here. </strong></p>
            </div>
          </template>
        </FileUpload>
      </div>
    </div>
  </div>
</template>
