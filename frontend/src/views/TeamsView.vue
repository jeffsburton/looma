<script setup>
import { ref } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import Button from 'primevue/button'

// Static demo data per requirements
const teams = ref([
  {
    name: 'Alpha',
    mascot: { emoji: '🦅', bg: '#E0F2FE' },
    members: [
      { name: 'Ava Stone', photoUrl: '/images/sample_faces/1.png' },
      { name: 'Ben Carter', photoUrl: '/images/sample_faces/2.png' },
      { name: 'Clara Ruiz', photoUrl: '/images/sample_faces/3.png' },
    ],
    cases: [
      { name: 'Kendrick Owen', photoUrl: '/images/sample_faces/1.png' },
      { name: 'Jasmine Jackson', photoUrl: '/images/sample_faces/2.png' },
    ]
  },
  {
    name: 'Bravo',
    mascot: { emoji: '🐺', bg: '#ECFDF5' },
    members: [
      { name: 'Diego Mendez', photoUrl: '/images/sample_faces/4.png' },
      { name: 'Ella Harper', photoUrl: '/images/sample_faces/1.png' },
      { name: 'Finn O’Connor', photoUrl: '/images/sample_faces/2.png' },
    ],
    cases: [
      { name: 'Chaz Hernandez', photoUrl: '/images/sample_faces/3.png' },
      { name: 'Tanya Rider', photoUrl: '/images/sample_faces/4.png' },
    ]
  },
  {
    name: 'Charlie',
    mascot: { emoji: '🐯', bg: '#FEF3C7' },
    members: [
      { name: 'Grace Lin', photoUrl: '/images/sample_faces/3.png' },
      { name: 'Hank Porter', photoUrl: '/images/sample_faces/4.png' },
      { name: 'Ivy Chen', photoUrl: '/images/sample_faces/1.png' },
    ],
    cases: [
      { name: 'Mara Quinn', photoUrl: '/images/sample_faces/2.png' },
      { name: 'Dylan Keane', photoUrl: '/images/sample_faces/3.png' },
    ]
  },
  {
    name: 'Apex',
    mascot: { emoji: '🦈', bg: '#EDE9FE' },
    members: [
      { name: 'Jon Park', photoUrl: '/images/sample_faces/2.png' },
      { name: 'Kira Novak', photoUrl: '/images/sample_faces/3.png' },
      { name: 'Liam Ford', photoUrl: '/images/sample_faces/4.png' },
    ],
    cases: [
      { name: 'Renee Holt', photoUrl: '/images/sample_faces/1.png' },
      { name: 'Noah Ellis', photoUrl: '/images/sample_faces/4.png' },
    ]
  },
])

// Track which teams are expanded
const open = ref(new Set())
const toggle = (name) => {
  const s = new Set(open.value)
  if (s.has(name)) s.delete(name)
  else s.add(name)
  open.value = s
}
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Teams'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <!-- Header -->
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Teams</div>
            <Button label="Add Team" icon="pi pi-plus" />
          </div>

          <!-- Content panel -->
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <ul class="list-none p-0 m-0 flex flex-column gap-2">
              <li v-for="team in teams" :key="team.name" class="border-1 surface-border border-round">
                <!-- Team header row -->
                <button class="w-full p-2 flex align-items-center gap-2 cursor-pointer border-none bg-transparent text-left" @click="toggle(team.name)">
                  <span class="material-symbols-outlined text-700" aria-hidden="true">{{ open.has(team.name) ? 'expand_less' : 'expand_more' }}</span>
                  <span class="mascot" :style="{ background: team.mascot.bg }" aria-hidden="true">{{ team.mascot.emoji }}</span>
                  <span class="font-medium text-900">{{ team.name }}</span>
                </button>

                <!-- Expanded panel -->
                <div v-if="open.has(team.name)" class="p-2 pt-0">
                  <div class="grid" style="gap: 1rem">
                    <!-- Team Members -->
                    <section class="col-12 md:col-6">
                      <div class="text-800 font-semibold mb-2">Team Members</div>
                      <ul class="list-none p-0 m-0 flex flex-column gap-1">
                        <li v-for="m in team.members" :key="m.name" class="flex align-items-center gap-2 p-1 border-round hover:surface-100">
                          <img :src="m.photoUrl" :alt="m.name" class="avatar" />
                          <span class="text-900">{{ m.name }}</span>
                        </li>
                      </ul>
                    </section>

                    <!-- Cases -->
                    <section class="col-12 md:col-6">
                      <div class="text-800 font-semibold mb-2">Cases</div>
                      <ul class="list-none p-0 m-0 flex flex-column gap-1">
                        <li v-for="c in team.cases" :key="c.name" class="flex align-items-center gap-2 p-1 border-round hover:surface-100">
                          <img :src="c.photoUrl" :alt="c.name" class="avatar" />
                          <span class="text-900">{{ c.name }}</span>
                        </li>
                      </ul>
                    </section>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mascot {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.avatar {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  object-fit: cover;
}
button { outline: none; }
</style>
