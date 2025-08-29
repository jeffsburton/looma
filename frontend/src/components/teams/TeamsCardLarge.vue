<script setup>
import Button from 'primevue/button'

const props = defineProps({
  team: { type: Object, required: true },
  canModify: { type: Boolean, default: false }
})

const emit = defineEmits(['edit'])
</script>

<template>
  <div class="team-card p-2 border-1 surface-border border-round">
    <div class="flex align-items-center justify-content-between gap-2 mb-2">
      <div class="flex align-items-center gap-2 min-w-0">
        <img v-if="team.photo_url" :src="team.photo_url" :alt="team.name" class="team-avatar" />
        <button class="name-button" @click="emit('edit', team)">
          <span class="font-semibold text-lg text-900">{{ team.name }}</span>
          <div v-if="team.event_name" class="text-700 text-sm">{{ team.event_name }}</div>
        </button>
      </div>
      <div class="flex align-items-center gap-2">
        <span v-if="team.inactive" class="text-600 text-sm">Inactive</span>
        <Button v-if="canModify" icon="pi pi-pencil" size="small" text @click="emit('edit', team)" />
      </div>
    </div>

    <div class="grid" style="gap: 1rem">

      <section class="col-12 md:col-12">
        <div class="text-800 font-semibold mb-2">Cases</div>
        <div v-if="team.cases?.length" class="flex flex-column gap-1">
          <div v-for="c in team.cases" :key="c.id || c.name" class="flex flex-nowrap align-items-center gap-2 p-1 border-round hover:surface-100 w-full">
            <img v-if="c.photo_url" :src="c.photo_url" :alt="c.name" class="case-avatar" />
            <span class="text-900 flex-1 min-w-0 name-clip text-lg font-medium case-name">{{ c.name }}</span>
          </div>
        </div>
        <div v-else class="text-600 text-sm">No cases</div>
      </section>
      <section class="col-12 md:col-12">
        <div class="text-800 font-semibold mb-2">Team Members</div>
        <div v-if="team.members?.length" class="flex flex-column gap-1">
          <div v-for="m in team.members" :key="m.id || m.name" class="flex flex-nowrap align-items-center gap-2 p-1 border-round hover:surface-100 w-full">
            <img v-if="m.photo_url" :src="m.photo_url" :alt="m.name" class="avatar" />
            <span class="text-900 flex-1 min-w-0 name-clip">{{ m.name }}</span>
          </div>
        </div>
        <div v-else class="text-600 text-sm">No members</div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.name-button { background: transparent; border: none; padding: 0; cursor: pointer; text-align: left; }
.avatar { width: 28px; height: 28px; border-radius: 999px; object-fit: cover; }
.team-avatar { width: 36px; height: 36px; border-radius: 999px; object-fit: cover; }
.case-avatar { width: 40px; height: 40px; border-radius: 999px; object-fit: cover; }
.name-clip { display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
