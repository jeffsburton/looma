<script setup>
import { ref } from 'vue'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'

// A simple local form model. In the future this can be lifted to a store/parent.
const ynu = [
  { label: 'Yes', value: 'Yes' },
  { label: 'No', value: 'No' },
  { label: 'Unknown', value: 'Unknown' }
]

const form = ref({
  // Narrative
  whoWith: '',
  whatHappened: '',
  confideIn: '',

  // General Questions
  neighborsCameras: null,
  neighborsCamerasNotes: '',
  haveTheyRunBefore: null,
  noteFound: null,
  favoritePlaces: '',

  // Known
  mentalHealthIssues: null,
  medicalIssues: null,
  prescriptionMeds: null,
  sexuallyActive: null,
  illicitDrugsAlcohol: null,
  knownNotes: '',

  // Experienced
  anyTrauma: null,
  majorCatastrophe: null,
  lossOfLovedOne: null,
  breakUp: null,
  abuse: null,
  experiencedNotes: '',

  // Behavior
  talkedAboutSelfHarm: null,
  behaviorChanges: null,
  recklessOrAggressive: null,
  withdrawingFromActivities: null,
  sleepingHabitsChanged: null,
  behaviorNotes: '',

  // Is it possible
  electronicsUsedForUnknownContacts: null,
  receivedOrSentSexualImages: null,
  exploitedTraffickedPast: null,
  friendsExploitedTrafficked: null,
  showingUpWithItems: null,
  possibleNotes: '',

  // Interests and Likes
  gamer: null,
  archetype: '',
  belongToClubs: null,
  sexualityQuestioning: null,
  travelPlacesMentioned: '',
  interestsNotes: ''
})
</script>
<template>
  <div class="p-3">

    <!-- Narrative Top Questions -->
    <div class="grid formgrid p-fluid mb-4">
      <div class="col-12 md:col-4">
        <label class="block mb-2">Who were they with?</label>
        <InputText v-model="form.whoWith" placeholder="Names, relationships" />
      </div>
      <div class="col-12 md:col-8">
        <label class="block mb-2">What happened per reporting party?</label>
        <Textarea v-model="form.whatHappened" auto-resize rows="2" placeholder="Summary from reporting party" />
      </div>
      <div class="col-12">
        <label class="block mb-2">Who is the person(s) the MP would absolutely confide in?</label>
        <InputText v-model="form.confideIn" placeholder="Names, relationship, contact details if available" />
      </div>
    </div>

    <!-- General Questions -->
    <div class="surface-card border-round p-3 mb-4">
      <div class="font-medium mb-3">General Questions</div>
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-4">
          <label class="block mb-2">Do neighbors have cameras?</label>
          <Dropdown v-model="form.neighborsCameras" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-4">
          <label class="block mb-2">Have they run before?</label>
          <Dropdown v-model="form.haveTheyRunBefore" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-4">
          <label class="block mb-2">Has there been a note found?</label>
          <Dropdown v-model="form.noteFound" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Do they have favorite places they like to go, eat, hang out?</label>
          <InputText v-model="form.favoritePlaces" placeholder="List places" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Brief explanation (if needed)</label>
          <Textarea v-model="form.neighborsCamerasNotes" auto-resize rows="2" placeholder="Any relevant details (e.g., which neighbors, camera types)" />
        </div>
      </div>
    </div>

    <!-- Are there any known -->
    <div class="surface-card border-round p-3 mb-4">
      <div class="font-medium mb-3">Are there any known</div>
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-2">
          <label class="block mb-2">Mental health issues?</label>
          <Dropdown v-model="form.mentalHealthIssues" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-2">
          <label class="block mb-2">Medical issues?</label>
          <Dropdown v-model="form.medicalIssues" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-2">
          <label class="block mb-2">Prescription medications?</label>
          <Dropdown v-model="form.prescriptionMeds" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Sexually active?</label>
          <Dropdown v-model="form.sexuallyActive" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Illicit drugs or alcohol?</label>
          <Dropdown v-model="form.illicitDrugsAlcohol" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12">
          <label class="block mb-2">Brief explanation (if needed)</label>
          <Textarea v-model="form.knownNotes" auto-resize rows="2" placeholder="Provide examples, conditions, meds, substances, etc." />
        </div>
      </div>
    </div>

    <!-- Have they experienced -->
    <div class="surface-card border-round p-3 mb-4">
      <div class="font-medium mb-3">Have they experienced</div>
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-2">
          <label class="block mb-2">Any sort of trauma?</label>
          <Dropdown v-model="form.anyTrauma" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Major catastrophe (fire, MVA, severe injury, natural disaster)?</label>
          <Dropdown v-model="form.majorCatastrophe" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-2">
          <label class="block mb-2">Loss of a loved one</label>
          <Dropdown v-model="form.lossOfLovedOne" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-2">
          <label class="block mb-2">Break up</label>
          <Dropdown v-model="form.breakUp" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Abuse</label>
          <Dropdown v-model="form.abuse" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12">
          <label class="block mb-2">Brief explanation (if possible/needed)</label>
          <Textarea v-model="form.experiencedNotes" auto-resize rows="2" placeholder="Details (e.g., type of trauma, timing)" />
        </div>
      </div>
    </div>

    <!-- Behavior -->
    <div class="surface-card border-round p-3 mb-4">
      <div class="font-medium mb-3">Behavior</div>
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-3">
          <label class="block mb-2">Talked about hurting themselves?</label>
          <Dropdown v-model="form.talkedAboutSelfHarm" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Any changes in behavior?</label>
          <Dropdown v-model="form.behaviorChanges" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Acting recklessly or overly aggressive?</label>
          <Dropdown v-model="form.recklessOrAggressive" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Withdrawing from activities/friends?</label>
          <Dropdown v-model="form.withdrawingFromActivities" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-3">
          <label class="block mb-2">Sleeping habits changed?</label>
          <Dropdown v-model="form.sleepingHabitsChanged" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12">
          <label class="block mb-2">Brief explanation (if possible/needed)</label>
          <Textarea v-model="form.behaviorNotes" auto-resize rows="2" placeholder="Examples or observations" />
        </div>
      </div>
    </div>

    <!-- Is it possible -->
    <div class="surface-card border-round p-3 mb-4">
      <div class="font-medium mb-3">Is it possible</div>
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-4">
          <label class="block mb-2">Used electronics to interact with unknown persons?</label>
          <Dropdown v-model="form.electronicsUsedForUnknownContacts" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-4">
          <label class="block mb-2">Received or transmitted sexual images on the internet?</label>
          <Dropdown v-model="form.receivedOrSentSexualImages" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-4">
          <label class="block mb-2">Sexually exploited/trafficked in the past?</label>
          <Dropdown v-model="form.exploitedTraffickedPast" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Friends/acquaintances who may have been exploited/trafficked?</label>
          <Dropdown v-model="form.friendsExploitedTrafficked" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Showing up with items they cannot afford?</label>
          <Dropdown v-model="form.showingUpWithItems" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12">
          <label class="block mb-2">Brief explanation (if possible/needed)</label>
          <Textarea v-model="form.possibleNotes" auto-resize rows="2" placeholder="Devices, platforms, circumstances, items, etc." />
        </div>
      </div>
    </div>

    <!-- Interests and Likes -->
    <div class="surface-card border-round p-3">
      <div class="font-medium mb-3">Interests and Likes</div>
      <div class="grid formgrid p-fluid">
        <div class="col-12 md:col-2">
          <label class="block mb-2">Are they a gamer?</label>
          <Dropdown v-model="form.gamer" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-4">
          <label class="block mb-2">Archetype (goth, cheerleader, artsy, outdoorsy?)</label>
          <InputText v-model="form.archetype" placeholder="Describe" />
        </div>
        <div class="col-12 md:col-2">
          <label class="block mb-2">Belong to any clubs?</label>
          <Dropdown v-model="form.belongToClubs" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-4">
          <label class="block mb-2">Free spirit / questioning or confused over their sexuality?</label>
          <Dropdown v-model="form.sexualityQuestioning" :options="ynu" optionLabel="label" optionValue="value" placeholder="Select" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Have they mentioned places they would like to travel to?</label>
          <InputText v-model="form.travelPlacesMentioned" placeholder="List places" />
        </div>
        <div class="col-12 md:col-6">
          <label class="block mb-2">Brief explanation (if possible/needed)</label>
          <Textarea v-model="form.interestsNotes" auto-resize rows="2" placeholder="What games? Clubs? Details." />
        </div>
      </div>
    </div>
  </div>
</template>
