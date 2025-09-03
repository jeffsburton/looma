<script setup>
import { ref, watch, computed } from 'vue'
import FloatLabel from 'primevue/floatlabel'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import DatePicker from 'primevue/datepicker'
import ToggleSwitch from 'primevue/toggleswitch'
import Fieldset from 'primevue/fieldset'
import RefSelect from '../../../RefSelect.vue'

const props = defineProps({
  caseId: { type: String, default: '' },
})

// Local model for circumstances
const m = ref({
  date_missing: null,
  time_missing: null,
  date_reported: null,
  address: '',
  city: '',
  state_id: '',
  with_whom: '',
  what_happened: '',
  have_id_id: '',
  id_taken_id: '',
  have_money_id: '',
  money_taken_id: '',
  have_cc_id: '',
  cc_taken_id: '',
  vehicle_taken: false,
  vehicle_desc: '',
  clothing_top: '',
  clothing_bottom: '',
  clothing_shoes: '',
  clothing_outerwear: '',
  clothing_innerwear: '',
  bags: '',
  other_items: '',
  devices: '',
  mobile_carrier_id: '',
  voip_id: '',
  wifi_only: false,
})

let saveTimer = null
let loading = false
let hydrated = false // becomes true only after initial load completes to allow saves

function toDateOrNull(v) {
  if (!v) return null
  const d = v instanceof Date ? v : new Date(v)
  return isNaN(d.getTime()) ? null : d
}

const dateMissing = computed({
  get(){ return toDateOrNull(m.value.date_missing) },
  set(v){ m.value.date_missing = v instanceof Date ? v.toISOString().slice(0,10) : (v || null); queueSave() }
})

const dateReported = computed({
  get(){ return toDateOrNull(m.value.date_reported) },
  set(v){ m.value.date_reported = v instanceof Date ? v.toISOString() : (v || null); queueSave() }
})

// Time handling: store as ISO time string "HH:MM:SS" or ISO date-time acceptable by backend
const timeMissing = computed({
  get(){
    const t = m.value.time_missing
    if (!t) return null
    // Accept stored ISO string or Date
    return toDateOrNull(typeof t === 'string' ? `1970-01-01T${t}` : t)
  },
  set(v){
    if (!v) { m.value.time_missing = null; queueSave(); return }
    const d = v instanceof Date ? v : new Date(v)
    if (isNaN(d.getTime())) { m.value.time_missing = null; queueSave(); return }
    const hh = String(d.getHours()).padStart(2,'0')
    const mm = String(d.getMinutes()).padStart(2,'0')
    m.value.time_missing = `1970-01-01T${hh}:${mm}:00Z`
    queueSave()
  }
})

watch(() => props.caseId, (v) => { hydrated = false; if (v) load() }, { immediate: true })

// When vehicle is not taken, clear the description so we don't persist stale data
watch(() => m.value.vehicle_taken, (on) => {
  if (!on) m.value.vehicle_desc = ''
})

async function load(){
  if (!props.caseId) return
  try {
    loading = true
    hydrated = false
    const resp = await fetch(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/circumstances`, {
      headers: { 'Accept': 'application/json' },
      credentials: 'include',
    })
    if (resp.ok) {
      const data = await resp.json()
      // Normalize to local model
      m.value = {
        date_missing: data.date_missing || null,
        time_missing: data.time_missing || null,
        date_reported: data.date_reported || null,
        address: data.address || '',
        city: data.city || '',
        state_id: data.state_id != null ? String(data.state_id) : '',
        with_whom: data.with_whom || '',
        what_happened: data.what_happened || '',
        have_id_id: data.have_id_id != null ? String(data.have_id_id) : '',
        id_taken_id: data.id_taken_id != null ? String(data.id_taken_id) : '',
        have_money_id: data.have_money_id != null ? String(data.have_money_id) : '',
        money_taken_id: data.money_taken_id != null ? String(data.money_taken_id) : '',
        have_cc_id: data.have_cc_id != null ? String(data.have_cc_id) : '',
        cc_taken_id: data.cc_taken_id != null ? String(data.cc_taken_id) : '',
        vehicle_taken: !!data.vehicle_taken,
        vehicle_desc: data.vehicle_desc || '',
        clothing_top: data.clothing_top || '',
        clothing_bottom: data.clothing_bottom || '',
        clothing_shoes: data.clothing_shoes || '',
        clothing_outerwear: data.clothing_outerwear || '',
        clothing_innerwear: data.clothing_innerwear || '',
        bags: data.bags || '',
        other_items: data.other_items || '',
        devices: data.devices || '',
        mobile_carrier_id: data.mobile_carrier_id != null ? String(data.mobile_carrier_id) : '',
        voip_id: data.voip_id != null ? String(data.voip_id) : '',
        wifi_only: !!data.wifi_only,
      }
    } else {
      // Initialize fresh
      m.value = { ...m.value }
    }
  } finally {
    loading = false
    // Allow saves after the microtask so watchers have settled
    queueMicrotask(() => { hydrated = true })
  }
}

function queueSave(){
  if (!props.caseId) return
  if (!hydrated) return // do not save during initial hydration
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(save, 600)
}

watch(m, () => { queueSave() }, { deep: true })

async function save(){
  try {
    const payload = { ...m.value }
    // For backend compatibility: send strings for ref ids, booleans as is
    await fetch(`/api/v1/cases/${encodeURIComponent(String(props.caseId))}/circumstances`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    })
  } catch (e) {
    console.error('Failed to save circumstances', e)
  }
}
</script>

<template>
  <div class="p-3">
    <div class="surface-card border-round p-3">
      <Fieldset legend="Basics" class="mb-3">
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <DatePicker id="date-missing" v-model="dateMissing" date-format="yy-mm-dd" showIcon iconDisplay="input" class="w-full" />
              <label for="date-missing">Date Missing</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <DatePicker id="time-missing" v-model="timeMissing" timeOnly hourFormat="24" showTime class="w-full" />
              <label for="time-missing">Time Missing</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <DatePicker id="date-reported" v-model="dateReported" showTime hourFormat="24" showIcon iconDisplay="input" class="w-full" />
              <label for="date-reported">Date Reported</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <InputText id="addr" v-model="m.address" class="w-full" />
              <label for="addr">Address</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <InputText id="city" v-model="m.city" class="w-full" />
              <label for="city">City</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="state" code="STATE" v-model="m.state_id" />
              <label for="state">State</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-2">
          <div>
            <FloatLabel variant="on">
              <Textarea id="with-whom" v-model="m.with_whom" auto-resize rows="2" class="w-full" />
              <label for="with-whom">With whom</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <Textarea id="what-happened" v-model="m.what_happened" auto-resize rows="2" class="w-full" />
              <label for="what-happened">What happened</label>
            </FloatLabel>
          </div>
        </div>
      </Fieldset>

      <Fieldset legend="Resources" class="mb-3">
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="have-id" code="YNU" v-model="m.have_id_id" />
              <label for="have-id">Have ID</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="id-taken" code="YNU" v-model="m.id_taken_id" />
              <label for="id-taken">ID taken</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="have-money" code="YNU" v-model="m.have_money_id" />
              <label for="have-money">Have money</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="money-taken" code="YNU" v-model="m.money_taken_id" />
              <label for="money-taken">Money taken</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="have-cc" code="YNU" v-model="m.have_cc_id" />
              <label for="have-cc">Have credit card</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="cc-taken" code="YNU" v-model="m.cc_taken_id" />
              <label for="cc-taken">Credit card taken</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-2">
          <div class="flex align-items-center gap-2">
            <ToggleSwitch :inputId="'vehicle-taken'" v-model="m.vehicle_taken" />
            <label for="vehicle-taken">Vehicle taken</label>
          </div>
          <div v-if="m.vehicle_taken">
            <FloatLabel variant="on">
              <InputText id="vehicle-desc" v-model="m.vehicle_desc" class="w-full" />
              <label for="vehicle-desc">Vehicle description</label>
            </FloatLabel>
          </div>
        </div>
      </Fieldset>

      <Fieldset legend="Clothing" class="mb-3">
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <InputText id="cloth-top" v-model="m.clothing_top" class="w-full" />
              <label for="cloth-top">Top</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <InputText id="cloth-bottom" v-model="m.clothing_bottom" class="w-full" />
              <label for="cloth-bottom">Bottom</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <InputText id="cloth-shoes" v-model="m.clothing_shoes" class="w-full" />
              <label for="cloth-shoes">Shoes</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <InputText id="cloth-outer" v-model="m.clothing_outerwear" class="w-full" />
              <label for="cloth-outer">Outerwear</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <InputText id="cloth-inner" v-model="m.clothing_innerwear" class="w-full" />
              <label for="cloth-inner">Innerwear</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <InputText id="bags" v-model="m.bags" class="w-full" />
              <label for="bags">Bags</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-1">
          <div>
            <FloatLabel variant="on">
              <Textarea id="other-items" v-model="m.other_items" auto-resize rows="2" class="w-full" />
              <label for="other-items">Other items</label>
            </FloatLabel>
          </div>
        </div>
      </Fieldset>

      <Fieldset legend="Devices" class="mb-1">
        <div class="row row-1">
          <div>
            <FloatLabel variant="on">
              <Textarea id="devices" v-model="m.devices" auto-resize rows="2" class="w-full" />
              <label for="devices">Devices</label>
            </FloatLabel>
          </div>
        </div>
        <div class="row row-3">
          <div>
            <FloatLabel variant="on">
              <RefSelect id="mobile" code="MOBILE" v-model="m.mobile_carrier_id" />
              <label for="mobile">Mobile Carrier</label>
            </FloatLabel>
          </div>
          <div>
            <FloatLabel variant="on">
              <RefSelect id="voip" code="VOIP" v-model="m.voip_id" />
              <label for="voip">VOIP Provider</label>
            </FloatLabel>
          </div>
          <div class="flex align-items-center gap-2">
            <ToggleSwitch :inputId="'wifi-only'" v-model="m.wifi_only" />
            <label for="wifi-only">WiFi-only device</label>
          </div>
        </div>
      </Fieldset>
    </div>
  </div>
</template>

<style scoped>
.row { display: grid; gap: 1rem; margin-bottom: 1rem; grid-template-columns: 1fr; }
@media (min-width: 700px) {
  .row-1 { grid-template-columns: 1fr; }
  .row-2 { grid-template-columns: repeat(2, 1fr); }
  .row-3 { grid-template-columns: repeat(3, 1fr); }
}
</style>
