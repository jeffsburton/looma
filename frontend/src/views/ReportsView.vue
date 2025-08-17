<script setup>
import { ref } from 'vue'
import SidebarMenu from '../components/SidebarMenu.vue'
import Chart from 'primevue/chart'

// Which report is currently selected to render below
const selected = ref('') // '', 'ytd', 'historical'

const selectReport = (key) => {
  selected.value = key
}

// Pie chart data for Year-to-date Case Disposition
const pieData = {
  labels: ['Open', 'Closed by C2R', 'Closed by Govt Agency', 'Closed by Other NGO'],
  datasets: [
    {
      data: [15, 73, 82, 23],
      backgroundColor: ['#60a5fa', '#34d399', '#f59e0b', '#ef4444'],
      hoverBackgroundColor: ['#3b82f6', '#10b981', '#d97706', '#dc2626']
    }
  ]
}

// Stacked bar chart data for Historical Results
const barData = {
  labels: ['2021', '2022', '2023', '2024'],
  datasets: [
    {
      type: 'bar',
      label: 'Open',
      backgroundColor: '#60a5fa',
      data: [0, 1, 3, 6]
    },
    {
      type: 'bar',
      label: 'Closed by C2R',
      backgroundColor: '#34d399',
      data: [16, 27, 34, 42]
    },
    {
      type: 'bar',
      label: 'Closed by Govt Agency',
      backgroundColor: '#f59e0b',
      data: [29, 38, 45, 39]
    },
    {
      type: 'bar',
      label: 'Closed by Other NGO',
      backgroundColor: '#ef4444',
      data: [8, 14, 16, 18]
    }
  ]
}

const stackedOptions = {
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top'
    },
    tooltip: {
      mode: 'index',
      intersect: false
    }
  },
  responsive: true,
  scales: {
    x: {
      stacked: true
    },
    y: {
      stacked: true,
      beginAtZero: true
    }
  }
}
</script>

<template>
  <div class="min-h-screen surface-50">
    <div class="p-2 max-w-6xl mx-auto">
      <div class="flex gap-2">
        <!-- Sidebar -->
        <div class="flex-none">
          <SidebarMenu :active="'Reports'" />
        </div>

        <!-- Main Content -->
        <div class="flex-1 min-w-0 flex flex-column" style="min-height: calc(100vh - 2rem)">
          <div class="flex align-items-center justify-content-between gap-2 pb-2">
            <div class="text-xl font-semibold">Reports</div>
          </div>

          <div class="surface-card border-round p-2 flex-1 overflow-auto">
            <!-- Two links -->
            <div class="flex flex-column gap-2">
              <div class="link-row cursor-pointer p-2 border-round flex align-items-center gap-2" @click="selectReport('ytd')">
                <span class="material-symbols-outlined">pie_chart</span>
                <span class="font-medium">Year-to-date Case Disposition</span>
              </div>
              <div class="link-row cursor-pointer p-2 border-round flex align-items-center gap-2" @click="selectReport('historical')">
                <span class="material-symbols-outlined">bar_chart</span>
                <span class="font-medium">Historical Results</span>
              </div>
            </div>

            <!-- Render chart below when a link is selected -->
            <!-- Pie: 60% width and centered -->
            <div v-if="selected === 'ytd'" class="mt-3">
              <div class="pie-wrap">
                <Chart type="pie" :data="pieData" />
              </div>
            </div>
            <!-- Bar: taller container -->
            <div v-else-if="selected === 'historical'" class="mt-3">
              <Chart type="bar" :data="barData" :options="stackedOptions"  class="h-[30rem]" :canvasProps="{'role': 'img', 'height': '500px'}"/>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.link-row { background: var(--p-surface-50, #fafafa); }
.link-row:hover { background: var(--p-surface-100, #f5f5f5); }
.pie-wrap { width: 60%; margin: 0 auto; }
</style>
