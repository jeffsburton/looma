<!-- SearchWrapper.vue -->
<template>
  <div class="search-wrapper">
    <!-- Search UI -->
    <div class="search-bar">



      <template v-if="hits.length === 0">
        <div class="w-20rem max-w-full">
          <FloatLabel variant="on">
            <InputText id="searchEntry" v-model="searchQuery" class="w-full" @keydown.enter="performSearch"/>
            <label for="searchEntry">Search</label>
          </FloatLabel>
        </div>
        <Button label="Search" icon="pi pi-search" @click="performSearch" :disabled="loading" />
      </template>


      <!-- Navigation UI (only show when there are hits) -->
      <div v-if="hits.length > 0" class="search-navigation">
        <span>{{ currentIndex + 1 }} of {{ hits.length }}</span>
        <Button size="small" text @click="previousHit" :disabled="currentIndex <= 0" title="Previous" aria-label="Previous">
          <span class="material-symbols-outlined">chevron_left</span>
        </Button>
        <Button size="small" text @click="nextHit" :disabled="currentIndex >= hits.length - 1" title="Next" aria-label="Next">
          <span class="material-symbols-outlined">chevron_forward</span>
        </Button>
        <Button size="small" text @click="clearSearch" title="Cancel search" aria-label="Cancel search">
          <span class="material-symbols-outlined">cancel</span>
        </Button>
      </div>
    </div>

    <!-- Content Area - where searchable components live -->
    <div class="search-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import InputText from "primevue/inputtext";
import Button from "primevue/button";
import FloatLabel from "primevue/floatlabel";

// Map: id -> { methods, instance, uid }
const searchableComponents = ref(new Map())
// Map: instance uid -> id
const instanceUidToId = ref(new Map())

const searchQuery = ref('')
const hits = ref([])
const currentIndex = ref(0)
const loading = ref(false)

// API for child components to register themselves
const registerSearchable = (id, methods, instance) => {
  const record = { methods, instance, uid: instance?.uid }
  searchableComponents.value.set(id, record)
  if (record.uid != null) {
    instanceUidToId.value.set(record.uid, id)
  }
}

const unregisterSearchable = (id) => {
  const record = searchableComponents.value.get(id)
  if (record?.uid != null) {
    instanceUidToId.value.delete(record.uid)
  }
  searchableComponents.value.delete(id)
}

function notifyAncestorsOfHit(childId, hitsForChild) {
  const childRecord = searchableComponents.value.get(childId)
  if (!childRecord?.instance) return

  let parent = childRecord.instance.parent
  // Walk up the Vue component tree
  while (parent) {
    const ancestorId = instanceUidToId.value.get(parent.uid)
    if (ancestorId) {
      const ancestorRecord = searchableComponents.value.get(ancestorId)
      const fn = ancestorRecord?.methods?.childHadSearchHit
      if (typeof fn === 'function') {
        try {
          fn({ childId, hits: hitsForChild, query: searchQuery.value, uid: childRecord.instance.uid })
        } catch (e) {
          // Swallow to avoid breaking search due to handler errors
          // console.error('childHadSearchHit error', e)
        }
      }
    }
    parent = parent.parent
  }
}

// Search functionality
async function performSearch() {
  if (!searchQuery.value.trim()) return

  loading.value = true
  try {
    const allHits = []

    // Call search on all registered components
    for (const [componentId, record] of searchableComponents.value) {

      const methods = record?.methods
      if (methods?.search && typeof methods.search === 'function') {
        const componentHits = await methods.search(searchQuery.value)
        if (Array.isArray(componentHits) && componentHits.length > 0) {
          // Notify ancestors that this child had hits
          notifyAncestorsOfHit(componentId, componentHits)
          // Add component reference to each hit
          componentHits.forEach(hit => {
            hit.componentId = componentId
          })
          allHits.push(...componentHits)
        }
      }
    }

    hits.value = allHits
    currentIndex.value = 0
    if (hits.value.length > 0) {
      showCurrentHit()
    }
  } finally {
    loading.value = false
  }
}

function showCurrentHit() {
  if (hits.value[currentIndex.value]) {
    const hit = hits.value[currentIndex.value]
    const record = searchableComponents.value.get(hit.componentId)
    const component = record?.methods
    if (component && component.showSearchHit) {
      component.showSearchHit(hit)
    }
  }
}

function nextHit() {
  if (currentIndex.value < hits.value.length - 1) {
    currentIndex.value++
    showCurrentHit()
  }
}

function previousHit() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    showCurrentHit()
  }
}

function clearSearch() {
  searchQuery.value = ''
  hits.value = []
  currentIndex.value = 0

  // Clear highlights from all components
  for (const [, record] of searchableComponents.value) {
    const methods = record?.methods
    if (methods?.clearHighlights) {
      methods.clearHighlights()
    }
  }
}

// Provide the API to child components
provide('searchAPI', {
  register: registerSearchable,
  unregister: unregisterSearchable
})
</script>

<style>
.search-bar {
  padding: 1rem;
  border-bottom: 1px solid #ccc;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.search-navigation {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-left: 1rem;
}

.search-content {
  flex: 1;
  overflow: auto;
}
</style>