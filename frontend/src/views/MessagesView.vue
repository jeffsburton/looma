<script setup>
import { ref, computed, nextTick } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import Button from 'primevue/button'
import Textarea from 'primevue/textarea'

</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Messages'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">


        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
