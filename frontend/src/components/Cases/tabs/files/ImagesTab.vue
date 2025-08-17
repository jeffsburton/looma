<script setup>
import { ref } from 'vue'

// Placeholder images and metadata
const items = ref([
  {
    id: 1,
    date: '2025-08-14 10:22',
    who: 'J. Smith',
    where: 'Trailhead Parking Lot',
    notes: 'Vehicle seen at 10am. Plate partially obscured.',
    url: 'https://picsum.photos/seed/alpha/800/600',
    thumb: 'https://picsum.photos/seed/alpha/300/200'
  },
  {
    id: 2,
    date: '2025-08-15 16:05',
    who: 'K. Patel',
    where: 'Ridge Overlook',
    notes: 'Footprints heading northbound near overlook.',
    url: 'https://picsum.photos/seed/bravo/800/600',
    thumb: 'https://picsum.photos/seed/bravo/300/200'
  },
  {
    id: 3,
    date: '2025-08-16 08:41',
    who: 'D. Nguyen',
    where: 'Creek Crossing',
    notes: 'Backpack found close to the waterline.',
    url: 'https://picsum.photos/seed/charlie/800/600',
    thumb: 'https://picsum.photos/seed/charlie/300/200'
  }
])

const onAdd = () => {
  // Placeholder: in future, open upload dialog
  const n = items.value.length + 1
  const seed = Math.random().toString(36).slice(2, 8)
  items.value.unshift({
    id: Date.now(),
    date: new Date().toISOString().slice(0, 16).replace('T', ' '),
    who: 'You',
    where: 'Unknown',
    notes: 'New placeholder image entry.',
    url: `https://picsum.photos/seed/${seed}/800/600`,
    thumb: `https://picsum.photos/seed/${seed}/300/200`
  })
}

const downloadImage = async (item) => {
  try {
    // Fetch the image as a blob so we can apply a filename
    const res = await fetch(item.url, { mode: 'cors' })
    const blob = await res.blob()
    const blobUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl
    a.download = `image_${item.id}.jpg`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(blobUrl)
  } catch (e) {
    // Fallback: try direct download link
    const a = document.createElement('a')
    a.href = item.url
    a.target = '_blank'
    a.rel = 'noopener noreferrer'
    a.click()
  }
}
</script>
<template>
  <div class="p-3">
    <!-- Top bar with Add button -->
    <div class="flex align-items-center justify-content-between mb-3">
      <div class="text-lg font-semibold flex align-items-center">
        <span class="material-symbols-outlined mr-1">imagesmode</span>
        <span>Files • Images</span>
      </div>
      <button class="p-2 border-round flex align-items-center gap-2 add-btn" @click="onAdd">
        <span class="material-symbols-outlined">add</span>
        <span>Add</span>
      </button>
    </div>

    <!-- Data list of images -->
    <div class="grid gap-3">
      <div v-for="item in items" :key="item.id" class="surface-card border-round p-2 flex gap-3 item-row">
        <div class="thumb-wrapper">
          <img :src="item.thumb" alt="image" class="thumb" />
        </div>
        <div class="flex-1">
          <div class="flex justify-content-between align-items-start">
            <div class="text-sm text-600">{{ item.date }}</div>
            <button class="icon-btn" @click="downloadImage(item)" :title="`Download image ${item.id}`">
              <span class="material-symbols-outlined">download</span>
            </button>
          </div>
          <div class="mt-1">
            <div class="text-md font-medium">
              <span class="text-700">Who:</span> {{ item.who }}
            </div>
            <div class="text-md">
              <span class="text-700">Where:</span> {{ item.where }}
            </div>
            <div class="text-md text-700">Notes</div>
            <div class="text-600">{{ item.notes }}</div>
          </div>
        </div>
      </div>

      <div v-if="items.length === 0" class="text-600">No images yet.</div>
    </div>
  </div>
</template>

<style scoped>
.add-btn {
  background: var(--p-primary-color, #2f80ed);
  color: #fff;
  border: 1px solid var(--p-primary-600, #2b6cb0);
}
.add-btn:hover {
  filter: brightness(0.95);
}
.item-row { min-height: 140px; }
.thumb-wrapper { width: 180px; flex: 0 0 180px; }
.thumb { width: 100%; height: 120px; object-fit: cover; border-radius: .5rem; }
.icon-btn { background: transparent; border: none; color: var(--p-text-color); cursor: pointer; padding: .25rem; border-radius: .375rem; }
.icon-btn:hover { background: var(--p-surface-100, #f5f5f5); }
@media (max-width: 640px) {
  .thumb-wrapper { width: 120px; flex-basis: 120px; }
  .thumb { height: 90px; }
}
</style>
