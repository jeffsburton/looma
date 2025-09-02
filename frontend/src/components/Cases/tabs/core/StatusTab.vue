<script setup>
import { ref, computed } from 'vue'
import InputSwitch from 'primevue/inputswitch'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import MultiSelect from 'primevue/multiselect'

// Local form model
const form = ref({
  found: false,
  archive: false,
  foundBy: null,
  dateFound: null,
  condition: null,
  exploitation: []
})

const foundByOptions = [
  'Called2Rescue',
  'Government Agency',
  'Other NGO',
  'Family',
  'Self',
  'Unknown'
].map(v => ({ label: v, value: v }))

const conditionOptions = [
  { label: 'Healthy', value: 'Healthy' },
  { label: 'Unhealth', value: 'Unhealth' },
  { label: 'Deceased', value: 'Deceased' }
]

const exploitationOptions = [
  'Physical',
  'Sexual',
  'CSAM',
  'CSEC'
].map(v => ({ label: v, value: v }))

// Controls after Archive are disabled until Found is toggled on
const disabledAfterArchive = computed(() => !form.value.found)
</script>

<template>
  <div class="p-3">

    <div class="surface-card border-round p-3">
      <div class="grid formgrid p-fluid">
        <!-- Found -->
        <div class="col-12 md:col-3">
          <label class="block mb-2">Found</label>
          <div class="flex align-items-center gap-2">
            <InputSwitch v-model="form.found" :inputId="'found'" />
            <label for="found">{{ form.found ? 'Yes' : 'No' }}</label>
          </div>
        </div>

        <!-- Archive -->
        <div class="col-12 md:col-3">
          <label class="block mb-2">Archive</label>
          <div class="flex align-items-center gap-2">
            <InputSwitch v-model="form.archive" :inputId="'archive'" />
            <label for="archive">{{ form.archive ? 'Yes' : 'No' }}</label>
          </div>
        </div>

        <!-- Found by -->
        <div class="col-12 md:col-6">
          <label class="block mb-2">Found by</label>
          <Dropdown v-model="form.foundBy"
                    :options="foundByOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select"
                    class="w-full"
                    :disabled="disabledAfterArchive" />
        </div>

        <!-- Date found -->
        <div class="col-12 md:col-4">
          <label class="block mb-2">Date found</label>
          <Calendar v-model="form.dateFound"
                    date-format="M d, yy"
                    show-icon
                    icon-display="input"
                    placeholder="Select date"
                    :disabled="disabledAfterArchive" />
        </div>

        <!-- Condition -->
        <div class="col-12 md:col-4">
          <label class="block mb-2">Condition</label>
          <Dropdown v-model="form.condition"
                    :options="conditionOptions"
                    optionLabel="label"
                    optionValue="value"
                    placeholder="Select"
                    class="w-full"
                    :disabled="disabledAfterArchive" />
        </div>

        <!-- Exploitation -->
        <div class="col-12 md:col-4">
          <label class="block mb-2">Exploitation</label>
          <MultiSelect v-model="form.exploitation"
                       :options="exploitationOptions"
                       optionLabel="label"
                       optionValue="value"
                       placeholder="Select one or more"
                       display="chip"
                       class="w-full"
                       :disabled="disabledAfterArchive" />
        </div>
      </div>
    </div>
  </div>
</template>
