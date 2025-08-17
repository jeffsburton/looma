<script setup>
import SidebarMenu from '../components/SidebarMenu.vue'
import CaseEdit from '../components/Cases/CaseEdit.vue'
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Cases'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <CaseEdit />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
