<script setup>
import { ref, reactive, onMounted } from 'vue'
import RefSelect from '../../../RefSelect.vue'
import Textarea from 'primevue/textarea'

const props = defineProps({
  caseId: { type: String, required: true },
})

const loading = ref(true)
const catalog = ref([]) // [{id, category, questions: [{id, question, follow_up}]}]
const answers = reactive({}) // victimology_id (opaque) -> { answer_id, details }

async function loadData() {
  loading.value = true
  try {
    const [catResp, ansResp] = await Promise.all([
      fetch('/api/v1/cases/victimology/catalog', { headers: { 'Accept': 'application/json' } }),
      fetch(`/api/v1/cases/${encodeURIComponent(props.caseId)}/victimology`, { headers: { 'Accept': 'application/json' } }),
    ])

    // Catalog
    let catData = []
    try {
      if (catResp.ok) {
        const j = await catResp.json()
        catData = Array.isArray(j) ? j : []
      }
    } catch (_) {
      catData = []
    }
    catalog.value = catData

    // Answers
    let ansData = []
    try {
      if (ansResp.ok) {
        const j = await ansResp.json()
        ansData = Array.isArray(j) ? j : []
      }
    } catch (_) {
      ansData = []
    }

    // Initialize default answers for all questions
    for (const cat of catalog.value) {
      for (const q of (cat.questions || [])) {
        if (!answers[q.id]) {
          answers[q.id] = { answer_id: null, details: '' }
        }
      }
    }
    // Merge existing stored answers
    for (const r of ansData) {
      answers[r.victimology_id] = { answer_id: r.answer_id || null, details: r.details || '' }
    }
  } finally {
    loading.value = false
  }
}

function ensureAnswer(victimologyId) {
  if (!answers[victimologyId]) {
    answers[victimologyId] = { answer_id: null, details: '' }
  }
}

async function upsert(victimologyId) {
  ensureAnswer(victimologyId)
  const body = {
    answer_id: answers[victimologyId].answer_id || null,
    details: answers[victimologyId].details || null,
  }
  await fetch(`/api/v1/cases/${encodeURIComponent(props.caseId)}/victimology/${encodeURIComponent(victimologyId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    body: JSON.stringify(body),
  })
}

onMounted(loadData)
</script>
<template>
  <div class="p-3">
    <div v-if="loading">Loading...</div>
    <div v-else>
      <fieldset v-for="cat in catalog" :key="cat.id" class="surface-card border-round p-3 mb-4">
        <legend class="font-medium">{{ cat.category }}</legend>
        <div v-for="q in cat.questions" :key="q.id" class="mb-3">
          <div class="mb-1">
            <div class="font-medium">{{ q.question }}</div>
            <div v-if="q.follow_up" class="text-500 text-sm">{{ q.follow_up }}</div>
          </div>
          <div class="grid formgrid p-fluid">
            <div class="col-12 md:col-3">
              <RefSelect
                :code="'YNUM'"
                v-model="answers[q.id].answer_id"
                placeholder="Select"
                @change="() => upsert(q.id)"
              />
            </div>
            <div class="col-12 md:col-9">
              <Textarea
                v-model="answers[q.id].details"
                auto-resize
                rows="2"
                placeholder="Details"
                class="w-full"
                @change="() => upsert(q.id)"
              />
            </div>
          </div>
          <div class="surface-border border-top-1 my-2"></div>
        </div>
      </fieldset>
    </div>
  </div>
</template>
