<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import SelectButton from 'primevue/selectbutton'
import Dialog from 'primevue/dialog'
import FileUpload from 'primevue/fileupload'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import FloatLabel from 'primevue/floatlabel'
import Button from "primevue/button";
import { reactive } from 'vue';
import ProgressBar from 'primevue/progressbar'
import Message from 'primevue/message'
import Badge from 'primevue/badge'
import Toast from 'primevue/toast'
import CaseSubjectSelect from '@/components/cases/CaseSubjectSelect.vue'
import SubjectPanel from '@/components/contacts/Subject.vue'

import api from '@/lib/api'

import { usePrimeVue } from 'primevue/config';
import { useToast } from "primevue/usetoast";

const toast = useToast();
const $primevue = usePrimeVue();

const props = defineProps({
  caseId: { type: [String, Number], required: false }
})

// View mode options
const viewOptions = [
  { label: 'List', value: 'list', icon: 'list' },
  { label: 'Large', value: 'large', icon: 'crop_landscape' },
  { label: 'Medium', value: 'medium', icon: 'view_cozy' }
]
const viewMode = ref('list')

// Items loaded from backend
const items = ref([])

// Edit dialog state
const showDialog = ref(false)
const editing = ref(null)

// Image subjects management
const imgSubjects = ref([])
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
    // Load visible subjects and find matching by opaque id
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

async function loadImageSubjects() {
  if (!props.caseId || !editing.value?.id) return
  subjectsLoading.value = true
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(props.caseId)}/images/${encodeURIComponent(editing.value.id)}/subjects`)
    imgSubjects.value = Array.isArray(data) ? data : []
  } catch (e) {
    imgSubjects.value = []
  } finally {
    subjectsLoading.value = false
  }
}

async function addImageSubject(subjectId) {
  const sid = subjectId || newSubjectId.value
  if (!props.caseId || !editing.value?.id || !sid) return
  try {
    await api.post(
      `/api/v1/cases/${encodeURIComponent(props.caseId)}/images/${encodeURIComponent(editing.value.id)}/subjects`,
      { subject_id: sid },
      { headers: { 'Accept': 'application/json' } }
    )
    // reset selection after adding
    newSubjectId.value = ''
    await loadImageSubjects()
  } catch (e) {
    console.error(e)
  }
}

function onSelectNewSubject(v) {
  if (!v) return
  // Prevent duplicate selection of the same subject
  const alreadyLinked = imgSubjects.value?.some(s => s.subject_id === v)
  if (alreadyLinked) {
    try { toast.add({ severity: 'info', summary: 'Already added', detail: 'This subject is already linked to the image.', life: 2500 }) } catch (_) {}
    newSubjectId.value = ''
    return
  }
  addImageSubject(v)
}

async function deleteImageSubject(linkId) {
  if (!props.caseId || !editing.value?.id || !linkId) return
  try {
    await api.delete(`/api/v1/cases/${encodeURIComponent(props.caseId)}/images/${encodeURIComponent(editing.value.id)}/subjects/${encodeURIComponent(linkId)}`)
    imgSubjects.value = imgSubjects.value.filter(s => s.id !== linkId)
  } catch (e) {
    console.error(e)
  }
}

function openEdit(item) {
  editing.value = { ...item }
  showDialog.value = true
  // Load image-subject links for this image
  loadImageSubjects()
}

const saving = ref(false)
async function saveEdit() {
  if (!editing.value || !props.caseId) return
  try {
    saving.value = true
    const body = {
      source_url: editing.value.source_url ?? null,
      where: editing.value.where ?? null,
      notes: editing.value.notes ?? null,
      // rfi_id support can be added later when UI supports selecting RFI
    }
    const { data: updated } = await api.patch(
      `/api/v1/cases/${encodeURIComponent(props.caseId)}/images/${encodeURIComponent(editing.value.id)}`,
      body,
      { headers: { 'Accept': 'application/json' } }
    )
    // Ensure thumb remains available for UI
    updated.thumb = updated.thumb || updated.url
    const idx = items.value.findIndex(i => i.id === updated.id)
    if (idx !== -1) items.value[idx] = { ...items.value[idx], ...updated }
    showDialog.value = false
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

async function onUploadFiles(files, uploadedFiles) {
  if (!props.caseId) return

  // If not already set elsewhere, prepare overall total
  // totalSize.value = files.reduce((acc, f) => acc + f.size, 0)
  // amountCompleted.value = 0

  const filesToProcess = [...files]

  for (const file of filesToProcess) {
    try {
      const fd = new FormData()
      fd.append('file', file, file.name)

      // Also append the generated thumbnail as JPEG.
      // We can use the previewSrc(file) object URL and fetch it to a Blob.
      try {
        if (file.thumbBlob) {
          fd.append('thumbnail', file.thumbBlob, 'thumbnail.jpg')
        }
      } catch (e) {
        // If thumbnail generation failed, continue without it
        console.warn('Thumbnail generation failed:', e)
      }

      await api.post(
        `/api/v1/cases/${encodeURIComponent(props.caseId)}/images/upload`,
        fd,
        {
          // Axios will set multipart Content-Type boundary automatically
          onUploadProgress: (evt) => {
            // evt.loaded is bytes uploaded for this single request
            const loaded = evt.loaded || 0

            // If you want per-file progress, compute percent from file.size
            const filePercent = Math.min(100, (loaded / file.size) * 100)
            // update some per-file progress state if you track it

            // For overall progress across files, estimate as
            // (bytes uploaded for current file + bytes of previously finished files)
            const previouslyCompleted = amountCompleted.value - (amountCompleted._filePartial || 0)
            amountCompleted._filePartial = loaded
            const overall = previouslyCompleted + loaded
            totalSizePercent.value = Math.min(100, (overall / totalSize.value) * 100)
          },
          // Optional: support cancel/abort if needed
          // signal: yourAbortController.signal,
        }
      )

      // When file finished, finalize counters
      const prevPartial = amountCompleted._filePartial || 0
      amountCompleted.value += (file.size - prevPartial)
      amountCompleted._filePartial = 0
      totalSizePercent.value = Math.min(100, (amountCompleted.value / totalSize.value) * 100)

      toast.add({ severity: 'success', summary: 'Success', detail: `File ${file.name} Uploaded`, life: 3000 })

      const index = files.findIndex(f => f === file)
      if (index > -1) files.splice(index, 1)

      // Optionally collect returned file
      // uploadedFiles.push(response.data)
    } catch (e) {
      console.error(e)
      toast.add({ severity: 'error', summary: 'Upload failed', detail: `${file.name}: ${e?.message || e}`, life: 5000 })
    }
  }

  totalSizePercent.value = 0
  await loadImages() // refresh list with server-derived fields
}

// Extract a frame at `timeSec` (default nudges off 0 to avoid black frames).
// Returns a Promise<Blob> (JPEG by default).
function extractFrameFromURL(src, timeSec = 0.1, type = 'image/jpeg', quality = 0.9, targetWidth) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    video.preload = 'auto';
    video.muted = true;
    video.playsInline = true;      // iOS Safari
    video.crossOrigin = 'anonymous'; // needed for remote URLs with CORS
    video.src = src;

    const fail = (msg) => reject(new Error(msg));

    video.addEventListener('error', () => fail('Failed to load video'));

    video.addEventListener('loadedmetadata', () => {
      if (!video.videoWidth || !video.videoHeight) return fail('No video dimensions');

      // Nudge off 0s; cap to tiny fraction of duration if needed
      const t = Math.min(timeSec, Math.max(0.01, (video.duration || 1) * 0.01));

      const onSeeked = () => {
        const vw = video.videoWidth;
        const vh = video.videoHeight;

        let outW = vw;
        let outH = vh;
        if (targetWidth && targetWidth > 0) {
          outW = targetWidth;
          outH = Math.round((vh / vw) * outW);
        }

        const canvas = document.createElement('canvas');
        canvas.width = outW;
        canvas.height = outH;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, outW, outH);

        canvas.toBlob((blob) => {
          if (!blob) return fail('Canvas toBlob failed');
          resolve(blob);
        }, type, quality);
      };

      video.addEventListener('seeked', onSeeked, { once: true });

      try {
        video.currentTime = t;
      } catch {
        // Some browsers need loadeddata before seeking
        video.addEventListener('loadeddata', () => { video.currentTime = t; }, { once: true });
      }
    }, { once: true });
  });
}

// Convenience for local File objects (from <input> / PrimeVue FileUpload)
async function extractFrameFromFile(file, timeSec = 0.1, type = 'image/jpeg', quality = 0.9, targetWidth) {
  const url = URL.createObjectURL(file);
  try {
    return await extractFrameFromURL(url, timeSec, type, quality, targetWidth);
  } catch(e) {
    console.log(`Error extracting frame from video: {e}`);
  } finally {
    URL.revokeObjectURL(url);
  }
}


async function createThumbnail(file, type = 'image/jpeg', quality = 0.9, targetWidth = 100) {
  const url = URL.createObjectURL(file);

  return new Promise((resolve, reject) => {
    const img = new Image();

    img.onload = () => {
      try {
        // Calculate dimensions maintaining aspect ratio
        const aspectRatio = img.height / img.width;
        const targetHeight = Math.round(targetWidth * aspectRatio);

        // Create canvas
        const canvas = document.createElement('canvas');
        canvas.width = targetWidth;
        canvas.height = targetHeight;

        // Draw image to canvas
        const ctx = canvas.getContext('2d');

        // Fill with white background first (for transparency)
        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, targetWidth, targetHeight);

        ctx.drawImage(img, 0, 0, targetWidth, targetHeight);

        // Convert to blob
        canvas.toBlob((blob) => {
          URL.revokeObjectURL(url); // Clean up
          if (blob) {
            resolve(blob);
          } else {
            reject(new Error('Failed to create thumbnail blob'));
          }
        }, type, quality);
      } catch (error) {
        URL.revokeObjectURL(url);
        reject(error);
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };

    // Set crossOrigin before src for CORS support
    img.crossOrigin = 'anonymous';
    img.src = url;
  });
}

// Map File -> poster URL (blob)
const posters = reactive(new Map());
const keyOf = (f) => `${f.name}-${f.size}-${f.type}-${f.lastModified || 0}`;

const previewSrc = (file) => {
  // use our poster for videos; for images, keep PrimeVue’s default objectURL

  return posters.get(keyOf(file))
};


const totalSize = ref(0);
const amountCompleted = ref(0);
const totalSizePercent = ref(0);
const files = ref([]);

const onRemoveFile = (file, removeFileCallback, index) => {
    removeFileCallback(index);
    totalSize.value -= file.size;
    if (totalSize.value < 0) totalSize.value = 0;
    totalSizePercent.value = 100 * (amountCompleted.value / totalSize.value);
    if (totalSizePercent.value < 1) totalSizePercent.value = 0;
    URL.revokeObjectURL(previewSrc(file));
};

const onClearUpload = (event) => {
    for(const file in files.value){
      URL.revokeObjectURL(previewSrc(file));
    }
    for(const file in files.value){
      URL.revokeObjectURL(previewSrc(file));
    }
    totalSize.value = 0;
    totalSizePercent.value = 0;
    amountCompleted.value = 0;
};

const onSelectedFiles = (event, fs, uploadedFiles) => {
    files.value = event.files;
    event.uploadedFiles = [];
    files.value.forEach( async (file) => {
        totalSize.value += file.size;
      let blob = null;
      if (file.type.startsWith('video/'))
        blob = await extractFrameFromFile(file, 0.12, 'image/jpeg', 0.9, 640); // 640px wide poster
      else
        blob = await createThumbnail(file);
      const thumbUrl = URL.createObjectURL(blob);
      file.thumbBlob = blob;
      posters.set(keyOf(file), thumbUrl);
    });
};

const formatSize = (bytes) => {
    const k = 1024;
    const dm = 3;
    const sizes = $primevue.config.locale.fileSizeTypes;

    if (bytes === 0) {
        return `0 ${sizes[0]}`;
    }

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const formattedSize = parseFloat((bytes / Math.pow(k, i)).toFixed(dm));

    return `${formattedSize} ${sizes[i]}`;
};


function isHighlighted(item) {
  return item.highlightedUntil && item.highlightedUntil > Date.now()
}

const isGrid = computed(() => viewMode.value === 'large' || viewMode.value === 'medium')
const tileClass = computed(() => viewMode.value === 'large' ? 'tile-large' : (viewMode.value === 'medium' ? 'tile-medium' : ''))

function formatDate(val) {
  if (!val) return ''
  try {
    return new Date(val).toLocaleString()
  } catch (e) {
    return String(val)
  }
}

function tooltipOptions(item) {
  const createdBy = item.created_by_name || '—'
  const fileName = item.file_name || '—'
  const rfi = item.rfi_name || '—'
  const where = item.where || '—'
  const sourceUrl = item.source_url || '—'
  const notes = item.notes || '-'
  const createdAt = formatDate(item.created_at)
  const subjects = Array.isArray(item.subjects) ? item.subjects : []

  const subjectsHtml = subjects.length
    ? `<div style='margin-top:.25rem;'><strong>People:</strong><div style='margin-top:.25rem;'>${subjects.map(s => `
          <div style='display:flex;align-items:center;gap:.5rem;margin:.125rem 0;'>
            <img src="${s.photo_url}" alt="${s.name}" style="width:20px;height:20px;border-radius:999px;object-fit:cover;" />
            <span>${s.name}</span>
          </div>`).join('')}</div></div>`
    : ''

  const html = `
    <div style="">
      <div><strong>Notes:</strong> ${notes}</div>
      <div><strong>Where:</strong> ${where}</div>
      <div><strong>Created By:</strong> ${createdBy}</div>
      <div><strong>File Name:</strong> ${fileName}</div>
      <div><strong>Source URL:</strong> ${sourceUrl !== '—' ? sourceUrl : '—'}</div>
      <div><strong>RFI:</strong> ${rfi}</div>
      ${createdAt ? `<div style='margin-top: .25rem;'><strong>Created At:</strong> ${createdAt}</div>` : ''}
      ${subjectsHtml}
    </div>
  `
  return { value: html, escape: false, class: "wide-tip"}
}

async function loadImages() {
  if (!props.caseId) { items.value = []; return }
  try {
    const { data } = await api.get(`/api/v1/cases/${encodeURIComponent(props.caseId)}/images`, { headers: { 'Accept': 'application/json' } })
    // Ensure thumb exists; reuse url for now
    items.value = Array.isArray(data) ? data.map(x => ({ ...x, thumb: x.thumb || x.url })) : []
  } catch (e) {
    console.error(e)
    items.value = []
  }
}

onMounted(loadImages)
watch(() => props.caseId, () => { loadImages() })

// Lightbox state and actions
const showLightbox = ref(false)
const lightboxItem = ref(null)

function openLightbox(item) {
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

function downloadItem(item) {
  try {
    const href = item?.url
    if (!href) return
    const a = document.createElement('a')
    a.href = href
    // Suggest a filename if available
    a.download = item?.file_name || 'download'
    a.rel = 'noopener'
    document.body.appendChild(a)
    a.click()
    a.remove()
  } catch (e) {
    // Fallback: open in a new tab
    try { window.open(item?.url, '_blank', 'noopener') } catch (_) { /* noop */ }
  }
}
</script>
<template>



  <div class="p-3">
    <!-- Controls row: Upload and View Mode selector -->
    <div class="flex align-items-center gap-3 mb-3 wrap">

      <!-- PrimeVue FileUpload -->
          <div class="w-full">
            <Toast />
            <FileUpload name="demo[]"
                        url="/api/upload"
                        :multiple="true"
                        accept="image/*,video/*"
                        :auto="false"
                        :maxFileSize="1000000000"
                        @select="onSelectedFiles($event, files, uploadedFiles)"
                        @clear="onClearUpload($event)"
                        adva
            >

                <template #header="{ chooseCallback, uploadCallback, clearCallback, files, uploadedFiles }">
                    <div class="flex flex-wrap justify-between items-center flex-1 gap-4">
                        <div class="flex gap-2">
                            <Button @click="chooseCallback()" class="file-upload-buttons"><i class="pi pi-plus"></i> Choose</Button>
                            <Button @click="onUploadFiles(files, uploadedFiles)" class="file-upload-buttons" severity="secondary" :disabled="!files || files.length === 0"><i class="pi pi-cloud-upload"></i> Upload</Button>
                            <Button @click="clearCallback()" class="file-upload-buttons" severity="secondary" :disabled="!files || files.length === 0"><i class="pi pi-times"></i> Clear</Button>
                        </div>
                        <ProgressBar :value="totalSizePercent" :showValue="false" class="md:w-20rem h-1 w-full md:ml-auto">
                            <span class="whitespace-nowrap">{{ totalSize }}B / 1Mb</span>
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
                              <div class="flex items-center gap-1">
                                <div class="shrink-0 items-center">
                                    <img role="presentation" :alt="file.name" :src="previewSrc(file)" :width="50" />
                                </div>
                                <div class="flex-1 min-w-0 align-content-center">
                                    <span class="font-semibold text-ellipsis whitespace-nowrap overflow-hidden block">{{ file.name }}</span>
                                    <div class="text-sm text-gray-600">{{ formatSize(file.size) }}</div>
                                </div>
                                <div class="shrink-0 align-content-center">
                                    <Badge value="Pending" severity="warn" />
                                </div>
                                <div class="shrink-0 align-content-center">
                                    <Button icon="pi pi-times" @click="onRemoveFile(file, removeFileCallback, index)" variant="outlined" rounded severity="danger" size="small" />
                                </div>
                              </div>
                            </div>
                        </div>
                    </div>
                </template>
                <template #empty>
                    <div class="flex items-center justify-center flex-col">
                        <p class="mt-1 mb-0">Drag and drop files to here to upload.</p>
                    </div>
                </template>
            </FileUpload>
        </div>

      <!-- View mode SelectButton -->
      <div class="flex-shrink-0 ml-auto">
        <SelectButton v-model="viewMode" :options="viewOptions" optionLabel="label" optionValue="value">
          <template #option="slotProps">
            <span class="material-symbols-outlined mr-1">{{ slotProps.option.icon }}</span>
            <span>{{ slotProps.option.label }}</span>
          </template>
        </SelectButton>
      </div>
    </div>

    <!-- Images rendering -->
    <div v-if="isGrid" class="image-grid" :class="tileClass">
      <div
        v-for="item in items"
        :key="item.id"
        class="image-tile"
        :class="{ highlighted: isHighlighted(item) }"
        @click="openLightbox(item)"
        role="button"
      >
        <!-- Hover action icons -->
        <div class="tile-actions" @click.stop>
          <button class="tile-icon" type="button" @click="openEdit(item)" v-tooltip.left="'Edit'">
            <i class="pi pi-pencil"></i>
          </button>
          <button class="tile-icon" type="button" @click="downloadItem(item)" v-tooltip.left="'Download'">
            <i class="pi pi-download"></i>
          </button>
        </div>
        <img :src="viewMode === 'large' && (!item.mime_type || !item.mime_type.includes('video')) ? item.url : item.thumb" alt="image" v-tooltip.bottom="tooltipOptions(item)" />
      </div>

      <div v-if="items.length === 0" class="text-600">No images yet.</div>
    </div>

    <div v-else class="list-view">
      <DataTable :value="items" dataKey="id" tableStyle="min-width: 680px" :rows="items?.length || 0">
        <Column header="Thumbnail" :exportable="false" style="width:120px">
          <template #body="{ data }">
            <img :src="data.thumb || data.url" alt="thumb" class="thumb" v-tooltip.bottom="tooltipOptions(data)" @click="openLightbox(data)" role="button" />
          </template>
        </Column>
        <Column field="notes" header="Notes">
          <template #body="{ data }">
            <span>{{ data.notes || '' }}</span>
          </template>
        </Column>
        <Column field="where" header="Where">
          <template #body="{ data }">
            <span>{{ data.where || '' }}</span>
          </template>
        </Column>
        <Column header="People">
          <template #body="{ data }">
            <div v-if="data.subjects && data.subjects.length" class="people-cell">
              <div v-for="s in data.subjects" :key="s.id" class="people-row clickable" @click.stop="openSubject(s.subject_id)">
                <img :src="s.photo_url" :alt="s.name" class="subject-avatar" />
                <span class="subject-name">{{ s.name }}</span>
              </div>
            </div>
            <span v-else class="text-600">—</span>
          </template>
        </Column>
        <Column header="" :exportable="false" style="width:64px; text-align:right;">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
            <Button icon="pi pi-download" size="small" text @click="downloadItem(data)" style="margin-left: .25rem;" />
          </template>
        </Column>
        <template #empty>
          <div class="text-600 p-2">No images yet.</div>
        </template>
      </DataTable>
    </div>

    <!-- Edit Dialog -->
    <Dialog v-model:visible="showDialog" modal header="Edit Image" :style="{ width: '480px' }">

      <div class="field pt-2">
        <FloatLabel variant="on">
          <Textarea id="img-notes" v-model="editing.notes" class="w-full" rows="2" autoResize placeholder="Description / context" />
          <label for="img-notes">Notes</label>
        </FloatLabel>
      </div>
      <div class="field">
        <FloatLabel variant="on">
          <Textarea id="img-where" v-model="editing.where" class="w-full" rows="2" autoResize placeholder="Location notes" />
          <label for="img-where">Where</label>
        </FloatLabel>
      </div>
      <div class="field">
        <FloatLabel variant="on">
          <InputText id="img-source-url" v-model="editing.source_url" class="w-full" placeholder="https://..." />
          <label for="img-source-url">Source URL</label>
        </FloatLabel>
      </div>
      <div class="grid-2 mt-2">
        <div>
          <div class="label">Created By</div>
          <div class="readonly">{{ editing.created_by_name || '—' }}</div>
        </div>
        <div>
          <div class="label">RFI</div>
          <div class="readonly">{{ editing.rfi_name || '—' }}</div>
        </div>
      </div>

      <!-- Subjects list and add -->
      <div class="field mt-3">
        <div class="label mb-2">Subjects in Image</div>
        <div v-if="subjectsLoading" class="text-600 text-sm mb-2">Loading…</div>
        <ul v-else class="subject-list">
          <li v-for="s in imgSubjects" :key="s.id" class="subject-row">
            <div class="subject-info clickable" @click.stop="openSubject(s.subject_id)">
              <img :src="s.photo_url" :alt="s.name" class="subject-avatar" />
              <span class="subject-name">{{ s.name }}</span>
            </div>
            <Button icon="pi pi-trash" text size="small" @click="deleteImageSubject(s.id)" />
          </li>
          <li v-if="imgSubjects.length === 0" class="text-600 text-sm">No subjects linked.</li>
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
        <button class="btn" @click="showDialog=false" :disabled="saving">Cancel</button>
        <button class="btn primary" @click="saveEdit" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      </template>
    </Dialog>

    <!-- Lightbox Overlay -->
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

    <!-- Subject Dialog -->
    <Dialog v-model:visible="subjectDialogVisible" modal header="Subject" :style="{ width: '640px' }">
      <div v-if="subjectLoading" class="p-3 text-600">Loading…</div>
      <SubjectPanel v-else-if="subjectModel" v-model="subjectModel" :isNew="false" :canModify="true" @updated="() => {}" @avatarChanged="() => {}" />
      <template #footer>
        <Button label="Close" text @click="subjectDialogVisible=false" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
/* Upload */
.upload-drop-area {
  display: flex; align-items: center; justify-content: center;
  padding: .75rem 1rem; border: 2px dashed var(--p-surface-400); border-radius: .5rem;
  color: var(--p-text-color, #6b7280);
}

/* View selector */
:deep(.p-selectbutton .p-button) { padding: .4rem .6rem; }

/* Grid views */
.image-grid { display: grid; gap: .75rem; }
.image-grid.tile-large { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
.image-grid.tile-medium { grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); }
.image-tile { position: relative; border-radius: .75rem; overflow: hidden; cursor: pointer; border: 2px solid transparent; aspect-ratio: 1 / 1; background: #fff; }
.image-tile img { position: absolute; inset: 0; height: 100%; object-fit: contain; background: #fff; display: block; border-radius: inherit; }

/* List view */
.list-view { display: flex; flex-direction: column; gap: .5rem; }
.list-row { display: flex; align-items: center; gap: .75rem; padding: .5rem; border-radius: .5rem; background: var(--p-surface-0); cursor: pointer; border: 2px solid transparent; }
.list-row .thumb { width: 50px; object-fit: cover; border-radius: .375rem; flex: 0 0 auto; }
/* Generic thumb size for table too */
.thumb { width: 50px; object-fit: cover; border-radius: .375rem; }
.list-row .notes { color: var(--p-text-color); }

/* Blue band highlight that fades after 10s */
@keyframes fadeBorder {
  0% { border-color: #3b82f6; }
  100% { border-color: transparent; }
}
.highlighted { border-color: #3b82f6 !important; animation: fadeBorder 10s ease-out forwards; }

/* Small icon button for table actions */
.icon-btn {
  background: transparent;
  border: none;
  padding: .25rem;
  border-radius: .375rem;
  cursor: pointer;
  color: var(--p-text-color);
}
.icon-btn:hover { background: var(--p-surface-200); }
.icon-btn .material-symbols-outlined { font-size: 20px; line-height: 1; vertical-align: middle; }




/* Tile hover actions */
.tile-actions {
  position: absolute;
  top: .4rem;
  right: .4rem;
  display: flex;
  gap: .35rem;
  opacity: 0;
  transition: opacity .15s ease-in-out;
  z-index: 2;
}
.image-tile:hover .tile-actions { opacity: 1; }
.tile-icon {
  background: rgba(255,255,255,0.9);
  border: 1px solid var(--p-surface-300);
  border-radius: .5rem;
  width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--p-text-color);
}
.tile-icon:hover { background: #fff; }
.tile-icon .pi { font-size: 14px; }

/* Lightbox */
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 1000;
}
.lightbox-close {
  position: fixed;
  top: 12px;
  right: 12px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.4);
  background: rgba(0,0,0,0.4);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1001;
}
.lightbox-close .pi { font-size: 18px; }
.lightbox-center {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2vw;
}
.lightbox-content {
  max-width: 80vw;
  max-height: 90vh;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lightbox-media {
  max-width: 80vw;
  max-height: 90vh;
  object-fit: contain;
  display: block;
}

/* Dialog */
.field { margin-bottom: .75rem; }
.label { font-size: .875rem; color: var(--p-text-color, #6b7280); margin-bottom: .25rem; display: block; }
.readonly { padding: .5rem .75rem; background: var(--p-surface-100); border-radius: .375rem; color: var(--p-text-color); }
.btn { background: var(--p-surface-200); color: var(--p-text-color); border: 1px solid var(--p-surface-300); border-radius: .375rem; padding: .4rem .75rem; margin-left: .5rem; }
.btn.primary { background: var(--p-primary-color); color: #fff; border-color: var(--p-primary-600); }

/* Responsive */
.wrap { flex-wrap: wrap; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; }
@media (max-width: 640px) {
  .grid-2 { grid-template-columns: 1fr; }
}

.file-upload-buttons {
  width: auto;
  padding-inline-start: 8px;
  padding-inline-end: 8px;
}

.subject-list { list-style: none; padding: 0; margin: 0; }
.subject-row { display: flex; align-items: center; justify-content: space-between; padding: .25rem 0; border-bottom: 1px solid var(--p-surface-200); }
.subject-row:last-child { border-bottom: 0; }
.subject-info { display: flex; align-items: center; gap: .5rem; min-width: 0; flex: 1 1 auto; }
.subject-avatar { width: 24px; height: 24px; border-radius: 999px; object-fit: cover; }
.subject-name { flex: 1 1 auto; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* List-view People cell */
.people-cell { display: flex; flex-direction: column; gap: .25rem; }
.people-row { display: flex; align-items: center; gap: .5rem; min-width: 0; }
.clickable { cursor: pointer; }
.clickable:hover .subject-name { text-decoration: underline; }

</style>
