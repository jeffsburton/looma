<script setup>
import { ref, computed } from 'vue'

import InputText from 'primevue/inputtext'
import Calendar from 'primevue/calendar'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'

const form = ref({
  firstName: '',
  middleName: '',
  lastName: '',
  nicknames: '',
  dob: null,
  dateMissing: null,
  timeMissing: '',
  dateReported: null,
  intakeDate: null,
  homeAddress: '',
  city: '',
  state: '',
  pointLastSeen: '',
  hasIDTaken: false,
  moneyTaken: '',
  cardsTaken: '',
  vehicleTaken: '',
  vehicleMakeModel: ''
})

const states = [
  'Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming'
].map(s => ({ label: s, value: s }))

const ageYears = computed(() => {
  const d = form.value.dob
  if (!d) return ''
  const now = new Date()
  let years = now.getFullYear() - d.getFullYear()
  const hadBirthday = (now.getMonth() > d.getMonth()) || (now.getMonth() === d.getMonth() && now.getDate() >= d.getDate())
  if (!hadBirthday) years -= 1
  return `${years} year(s)`
})
</script>
<template>
  <div class="p-3">

    <div class="grid formgrid p-fluid">
      <!-- Names -->
      <div class="col-12 md:col-4">
        <label class="block mb-2">MP First Name</label>
        <InputText v-model="form.firstName" placeholder="First Name" />
      </div>
      <div class="col-12 md:col-4">
        <label class="block mb-2">Middle</label>
        <InputText v-model="form.middleName" placeholder="Middle Name" />
      </div>
      <div class="col-12 md:col-4">
        <label class="block mb-2">Last</label>
        <InputText v-model="form.lastName" placeholder="Last Name" />
      </div>

      <div class="col-12 md:col-4">
        <label class="block mb-2">Nickname(s)</label>
        <InputText v-model="form.nicknames" placeholder="Nickname(s)" />
      </div>

      <!-- Dates and Age -->
      <div class="col-12 md:col-4">
        <label class="block mb-2">DOB</label>
        <Calendar v-model="form.dob" date-format="MM d, yy" show-icon icon-display="input" placeholder="Select date" />
      </div>
      <div class="col-12 md:col-4">
        <label class="block mb-2">Age</label>
        <InputText :value="ageYears" disabled />
      </div>

      <div class="col-12 md:col-4">
        <label class="block mb-2">Date Missing</label>
        <Calendar v-model="form.dateMissing" date-format="M d, yy" show-icon icon-display="input" placeholder="Select date" />
      </div>
      <div class="col-12 md:col-4">
        <label class="block mb-2">Time Missing</label>
        <InputText v-model="form.timeMissing" placeholder="e.g., 0700" />
      </div>
      <div class="col-12 md:col-4">
        <label class="block mb-2">Date Reported Missing</label>
        <Calendar v-model="form.dateReported" date-format="DD, M d, yy" show-icon icon-display="input" placeholder="Select date" />
      </div>

      <div class="col-12 md:col-4">
        <label class="block mb-2">Intake Date</label>
        <Calendar v-model="form.intakeDate" date-format="M d, yy" show-icon icon-display="input" placeholder="Select date" />
      </div>

      <!-- Address -->
      <div class="col-12 md:col-6">
        <label class="block mb-2">Home Address</label>
        <InputText v-model="form.homeAddress" placeholder="Street address" />
      </div>
      <div class="col-12 md:col-3">
        <label class="block mb-2">City Missing From</label>
        <InputText v-model="form.city" placeholder="City" />
      </div>
      <div class="col-12 md:col-3">
        <label class="block mb-2">State Missing From</label>
        <Dropdown v-model="form.state" :options="states" option-label="label" option-value="value" placeholder="Select State" filter />
      </div>

      <div class="col-12">
        <label class="block mb-2">Point Last Seen</label>
        <Textarea v-model="form.pointLastSeen" auto-resize rows="2" placeholder="Describe location last seen" />
      </div>

      <!-- Items taken / details -->
      <div class="col-12 md:col-6">
        <label class="block mb-2">Do they have ID / was the ID taken?</label>
        <div class="flex align-items-center gap-2">
          <Checkbox v-model="form.hasIDTaken" :binary="true" input-id="idTaken" />
          <label for="idTaken">ID Taken</label>
        </div>
      </div>
      <div class="col-12 md:col-6">
        <label class="block mb-2">Money / Money Taken?</label>
        <InputText v-model="form.moneyTaken" placeholder="Details (amount, description)" />
      </div>

      <div class="col-12 md:col-6">
        <label class="block mb-2">Debit or Credit Cards / Taken?</label>
        <InputText v-model="form.cardsTaken" placeholder="Details of cards" />
      </div>

      <div class="col-12 md:col-6">
        <label class="block mb-2">Vehicle Taken?</label>
        <InputText v-model="form.vehicleTaken" placeholder="Yes/No and basic details" />
      </div>

      <div class="col-12">
        <label class="block mb-2">Vehicle Make and Model</label>
        <InputText v-model="form.vehicleMakeModel" placeholder="e.g., Toyota Camry" />
      </div>
    </div>
  </div>
</template>
