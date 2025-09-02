<script setup>
import { computed, ref } from 'vue'
import Select from 'primevue/select'

// Standardized option sets with scores. Lower score = higher urgency.
// Note: These values are based on commonly used search-urgency style assessments.
// They are meant to guide prioritization and are not diagnostic.

const ageOptions = [
  { label: 'Child (0–12)', value: 1 },
  { label: 'Teen (13–16)', value: 2 },
  { label: 'Young Adult (17–24)', value: 3 },
  { label: 'Adult (25+)', value: 4 }
]

const physicalOptions = [
  { label: 'Injured/Ill/Reduced Mobility', value: 1 },
  { label: 'Unfit or Limited Stamina', value: 2 },
  { label: 'Average Fitness', value: 3 },
  { label: 'Fit/Endurance', value: 4 }
]

const medicalOptions = [
  { label: 'Critical/Time‑Sensitive Medical Needs', value: 1 },
  { label: 'Chronic Condition/Needs Medication', value: 2 },
  { label: 'Healthy/No Known Medical Needs', value: 3 },
  { label: 'Unknown', value: 2 }
]

const personalRiskOptions = [
  { label: 'Self‑harm risk/suicidal/acute mental health crisis', value: 1 },
  { label: 'History of running/high‑risk behavior/substance use', value: 2 },
  { label: 'Unknown', value: 3 },
  { label: 'No known history of risk', value: 4 }
]

const onlineRiskOptions = [
  { label: 'Known exploitation/trafficking', value: 1 },
  { label: 'Suspected exploitation or grooming', value: 2 },
  { label: 'Risky online contacts/unsupervised', value: 3 },
  { label: 'Minimal risk/monitored', value: 4 }
]

const familyDynamicsOptions = [
  { label: 'Violence/abuse OR drug/gang involvement by family', value: 1 },
  { label: 'Highly unstable/conflict', value: 2 },
  { label: 'Some conflict/strained', value: 3 },
  { label: 'Supportive/stable', value: 4 }
]

const behavioralOptions = [
  { label: 'Expressed self‑harm/intent to leave OR recent negative friend/peer change', value: 1 },
  { label: 'Significant withdrawal/aggression/recklessness', value: 2 },
  { label: 'Mild behavior changes', value: 3 },
  { label: 'No notable changes', value: 4 }
]

const form = ref({
  age: null,
  physical: null,
  medical: null,
  personalRisk: null,
  onlineRisk: null,
  family: null,
  behavioral: null
})

const selections = computed(() => [
  form.value.age,
  form.value.physical,
  form.value.medical,
  form.value.personalRisk,
  form.value.onlineRisk,
  form.value.family,
  form.value.behavioral
])

const total = computed(() => selections.value.reduce((sum, v) => sum + (typeof v === 'number' ? v : 0), 0))
const anyCritical = computed(() => selections.value.some(v => v === 1))
const complete = computed(() => selections.value.every(v => typeof v === 'number'))

const advisory = computed(() => {
  if (!complete.value) return 'Select one option for each category to calculate the total.'
  if (anyCritical.value) return 'Urgent Response may be required (one or more categories rated 1).'
  // Basic guidance by total; lower = more urgent
  if (total.value <= 12) return 'Urgent Response recommended.'
  if (total.value <= 17) return 'Priority Response.'
  return 'Standard Response.'
})
</script>
<template>
  <div class="p-3">

    <div class="surface-card border-round p-3">
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-6">
          <label class="block mb-2">Subject's Age</label>
          <Select v-model="form.age" :options="ageOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Physical Condition</label>
          <Select v-model="form.physical" :options="physicalOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>

        <div class="col-12 md:col-6">
          <label class="block mb-2">Medical Condition</label>
          <Select v-model="form.medical" :options="medicalOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Personal Risk Factors</label>
          <Select v-model="form.personalRisk" :options="personalRiskOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>

        <div class="col-12 md:col-6">
          <label class="block mb-2">Online Risk Factors</label>
          <Select v-model="form.onlineRisk" :options="onlineRiskOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Family Dynamics</label>
          <Select v-model="form.family" :options="familyDynamicsOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>

        <div class="col-12 md:col-6">
          <label class="block mb-2">Behavioral</label>
          <Select v-model="form.behavioral" :options="behavioralOptions" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
      </div>

      <hr class="my-3" />
      <div class="flex align-items-center justify-content-between gap-3">
        <div>
          <div class="font-medium">Total Score: <span>{{ total }}</span></div>
          <div class="text-600 text-sm">Lower total indicates greater urgency.</div>
        </div>
        <div class="text-right">
          <div class="font-medium">Assessment</div>
          <div class="text-600">{{ advisory }}</div>
        </div>
      </div>
      <div class="mt-2 text-600 text-sm">
        Guidance: The total typically ranges from 7 (most urgent) to 28 (least urgent). If any category is rated as 1, an urgent response may be needed regardless of total.
      </div>
    </div>
  </div>
</template>
