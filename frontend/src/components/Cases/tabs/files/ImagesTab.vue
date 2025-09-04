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

function openEdit(item) {
  editing.value = { ...item }
  showDialog.value = true
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
    const resp = await fetch(`/api/v1/cases/${encodeURIComponent(props.caseId)}/images/${encodeURIComponent(editing.value.id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body)
    })
    if (!resp.ok) throw new Error('Failed to save')
    const updated = await resp.json()
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

// Upload handling: POST files to backend; add highlight for 10s on returned items
async function onUploadFiles(event) {
  const files = Array.from(event.files || [])
  if (!props.caseId) return
  for (const file of files) {
    const fd = new FormData()
    fd.append('file', file, file.name)
    try {
      const resp = await fetch(`/api/v1/cases/${encodeURIComponent(props.caseId)}/images/upload`, {
        method: 'POST',
        body: fd,
        credentials: 'include'
      })
      if (!resp.ok) throw new Error('Upload failed')
      const created = await resp.json()
      created.thumb = created.url
      items.value.unshift(created)
    } catch (e) {
      console.error(e)
    }
  }
  // Refresh from server to populate created_by_name, rfi_name, etc.
  await loadImages()
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
  } finally {
    URL.revokeObjectURL(url);
  }
}


const onUploadSelect = async (e) => {
  for (const f of e.files) {
    if (f.type.startsWith('video/')) {
      try {
        const blob = await extractFrameFromFile(f, 0.12, 'image/jpeg', 0.9, 640); // 640px wide poster
        const thumbUrl = URL.createObjectURL(blob);


        console.log(thumbUrl);
        f.objectURL = thumbUrl;
        // use thumbUrl for preview or upload `blob`
        // remember to URL.revokeObjectURL(thumbUrl) when you’re done showing it
      } catch (err) {
        console.error('Frame extract failed:', err);
      }
    }
  }
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
  const html = `
    <div style="">
      <div><strong>Notes:</strong> ${notes}</div>
      <div><strong>Where:</strong> ${where}</div>
      <div><strong>Created By:</strong> ${createdBy}</div>
      <div><strong>File Name:</strong> ${fileName}</div>
      <div><strong>Source URL:</strong> ${sourceUrl !== '—' ? sourceUrl : '—'}</div>
      <div><strong>RFI:</strong> ${rfi}</div>
      ${createdAt ? `<div style='margin-top: .25rem;'><strong>Created At:</strong> ${createdAt}</div>` : ''}
    </div>
  `
  return { value: html, escape: false, class: "wide-tip"}
}

async function loadImages() {
  if (!props.caseId) { items.value = []; return }
  try {
    const resp = await fetch(`/api/v1/cases/${encodeURIComponent(props.caseId)}/images`, { credentials: 'include', headers: { 'Accept': 'application/json' } })
    if (!resp.ok) throw new Error('Failed to load images')
    const data = await resp.json()
    // Ensure thumb exists; reuse url for now
    items.value = Array.isArray(data) ? data.map(x => ({ ...x, thumb: x.thumb || x.url })) : []
  } catch (e) {
    console.error(e)
    items.value = []
  }
}

onMounted(loadImages)
watch(() => props.caseId, () => { loadImages() })
</script>
<template>



  <div class="p-3">
    <!-- Controls row: Upload and View Mode selector -->
    <div class="flex align-items-center gap-3 mb-3 wrap">

      <!-- PrimeVue FileUpload -->
      <div class="flex-1 min-w-0">
        <FileUpload
          name="images[]"
          mode="advanced"
          :multiple="true"
          :maxFileSize="1000000000"
          accept="image/*,video/*"
          :auto="false"
          customUpload
          @uploader="onUploadFiles"
          @select="onUploadSelect"
          chooseLabel="Choose"
          uploadLabel="Upload"
          cancelLabel="Clear"
        >
        <template #empty>
          <span>Drag and drop files to here to upload.</span>
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
        @click="openEdit(item)"
        role="button"
      >
        <img :src="viewMode === 'large' ? item.url : item.thumb" alt="image" v-tooltip.bottom="tooltipOptions(item)" />
      </div>
      <div v-if="items.length === 0" class="text-600">No images yet.</div>
    </div>

    <div v-else class="list-view">
      <DataTable :value="items" dataKey="id" tableStyle="min-width: 680px" :rows="items?.length || 0">
        <Column header="Thumbnail" :exportable="false" style="width:120px">
          <template #body="{ data }">
            <img :src="data.thumb || data.url" alt="thumb" class="thumb" v-tooltip.bottom="tooltipOptions(data)" />
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
        <Column field="url" header="Source">
          <template #body="{ data }">
            <span v-if="data.source_url">
              <a :href="data.source_url" target="_blank">
                {{data.source_url}}
               </a>
            </span>
          </template>
        </Column>
        <Column header="" :exportable="false" style="width:64px; text-align:right;">
          <template #body="{ data }">
            <Button icon="pi pi-pencil" size="small" text @click="openEdit(data)" />
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
      <template #footer>
        <button class="btn" @click="showDialog=false" :disabled="saving">Cancel</button>
        <button class="btn primary" @click="saveEdit" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
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
.image-grid.tile-medium { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
.image-tile { position: relative; border-radius: .5rem; overflow: hidden; cursor: pointer; border: 2px solid transparent; }
.image-tile img { display: block; width: 100%; height: 200px; object-fit: cover; }
.image-grid.tile-medium .image-tile img { height: 140px; }

/* List view */
.list-view { display: flex; flex-direction: column; gap: .5rem; }
.list-row { display: flex; align-items: center; gap: .75rem; padding: .5rem; border-radius: .5rem; background: var(--p-surface-0); cursor: pointer; border: 2px solid transparent; }
.list-row .thumb { width: 72px; height: 60px; object-fit: cover; border-radius: .375rem; flex: 0 0 auto; }
/* Generic thumb size for table too */
.thumb { width: 72px; height: 60px; object-fit: cover; border-radius: .375rem; }
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

</style>
