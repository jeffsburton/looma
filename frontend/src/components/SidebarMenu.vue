<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import api from '../lib/api'
import { getCookie, setCookie, deleteCookie } from '../lib/cookies'
// Sidebar for internal pages: vertical stack with Material icons.
// Handles logout internally by calling the API and clearing client state.

const props = defineProps({
  // Label of the active module to highlight (e.g., 'Home')
  active: { type: String, default: '' }
})

const router = useRouter()
const toast = useToast()

const COOKIE_KEY = 'ui_sidebar_collapsed'
const initialCollapsed = getCookie(COOKIE_KEY)
const collapsed = ref(initialCollapsed === '1' || initialCollapsed === 'true')
const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  // Persist preference for 1 year, cookie scoped to site root
  setCookie(COOKIE_KEY, collapsed.value ? '1' : '0', { maxAge: 60 * 60 * 24 * 365, sameSite: 'Lax' })
}

async function logout() {
  try {
    // Call backend logout endpoint; axios interceptor attaches Authorization from cookie if present
    await api.post('/api/v1/auth/logout')
  } catch (e) {
    // Per backend contract, logout is idempotent; even errors (e.g., no header) should not block UI logout
    // We intentionally ignore errors here and proceed to clear client state
  } finally {
    try {
      deleteCookie('access_token')
      localStorage.removeItem('user_email')
      localStorage.removeItem('user_name')
      localStorage.removeItem('is_authenticated')
    } catch (_) { /* noop */ }

    // Inform the user
    toast.add({
      severity: 'info',
      summary: 'Logged Out',
      detail: 'You have been logged out successfully',
      life: 3000
    })

    // Navigate to login
    router.push({ name: 'login' })
  }
}

// Top section items (excluding Account which is pinned to bottom)
const items = [
  { icon: 'cases', label: 'Cases' },
  { icon: '3p', label: 'Messages' },
  { icon: 'patient_list', label: 'Contacts' },
  { icon: 'list_alt_check', label: 'Tasks' },
  { icon: 'groups', label: 'Teams' },
  { icon: 'article', label: 'Reports' },
  { icon: 'settings', label: 'Admin' }
]
</script>

<template>
  <nav class="sidebar surface-card border-round p-2 flex flex-column">
    <!-- Top logo and brand -->
    <div class="logo-row flex align-items-center gap-2 mb-2">
      <img
        src="/images/shepherds-bug.png"
        alt="Shepherd's bug logo"
        class="sidebar-logo block"
      />
      <span v-show="!collapsed" class="brand text-900 font-semibold" aria-label="CALLED 2 RESCUE">
        <span class="brand-text">CALLED</span><span class="brand-digit">2</span><span class="brand-text">RESCUE</span>
      </span>
    </div>

    <!-- Top toggle -->
    <div class="toggle-btn p-2 border-round cursor-pointer mb-1 flex align-items-center justify-content-center"
         :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
         :title="collapsed ? 'Expand' : 'Collapse'"
         @click="toggleCollapsed">
      <span class="material-symbols-outlined text-700">{{ collapsed ? 'chevron_right' : 'chevron_left' }}</span>
    </div>

    <ul class="list-none m-0 p-0 flex flex-column gap-1">
      <li v-for="item in items" :key="item.label">
        <div
          class="menu-item p-2 border-round flex align-items-center gap-2 cursor-pointer"
          :class="[{ active: item.label === props.active, collapsed }]"
          @click="item.label === 'Cases' ? router.push({ name: 'cases' }) : item.label === 'Messages' ? router.push({ name: 'messages' }) : item.label === 'Contacts' ? router.push({ name: 'contacts' }) : item.label === 'Tasks' ? router.push({ name: 'tasks' }) : item.label === 'Teams' ? router.push({ name: 'teams' }) : item.label === 'Reports' ? router.push({ name: 'reports' }) : item.label === 'Admin' ? router.push({ name: 'admin' }) : null"
        >
          <span class="icon-wrap">
            <span :title="item.label" class="material-symbols-outlined">{{ item.icon }}</span>
            <span v-if="item.label === 'Messages'" class="badge" aria-label="7 unread messages">7</span>
            <span v-if="item.label === 'Tasks'" class="badge" aria-label="3 tasks">3</span>
          </span>
          <span v-show="!collapsed" class="label text-800 font-medium">{{ item.label }}</span>
        </div>
      </li>
    </ul>

    <div class="mt-auto pt-2 flex flex-column gap-1">
      <!-- Account pinned to bottom area -->
      <div
        class="menu-item p-2 border-round flex align-items-center gap-2 cursor-pointer"
        :class="[{ active: 'Account' === props.active, collapsed }]"
      >
        <span class="material-symbols-outlined">account_circle</span>
        <span v-show="!collapsed" class="label text-800 font-medium">Account</span>
      </div>

      <!-- Logout pinned to very bottom -->
      <div
        class="menu-item p-2 border-round flex align-items-center gap-2 cursor-pointer"
        :class="[{ collapsed }]"
        @click="logout"
      >
        <span class="material-symbols-outlined">logout</span>
        <span v-show="!collapsed" class="label text-800 font-medium">Logout</span>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.sidebar {
  width: max-content; /* only as wide as its content */
  height: calc(100vh - 18px); /* full viewport height to keep bottom icons visible */
  position: sticky; /* stay visible on page scroll */
  top: 0;
}
.sidebar-logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
}
.menu-item { color: var(--p-text-color, inherit); }
.menu-item:hover { background: var(--p-surface-100, #f5f5f5); }
.menu-item.active { background: var(--p-primary-100, #fbd5d5); color: var(--p-primary-700, #7f1d1d); }
.menu-item.active .material-symbols-outlined { color: var(--p-primary-700, #7f1d1d); }
.menu-item.collapsed { justify-content: center; }
.toggle-btn { background: var(--p-surface-100, #f5f5f5); }
.toggle-btn:hover { background: var(--p-surface-200, #eee); }
/* Make the middle menu list scrollable so bottom icons remain visible */
.sidebar > ul { flex: 1 1 auto; min-height: 0; overflow-y: auto; }

/* Badge on Messages icon */
.icon-wrap { position: relative; display: inline-flex; }
.badge {
  position: absolute;
  top: -4px;
  right: -6px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: 999px;
  background: var(--p-primary-500, #ef4444);
  color: #fff;
  font-size: 10px;
  line-height: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--p-surface-0, #fff);
}
/* Brand styling */
.logo-row .brand { text-transform: uppercase; font-size: 0.8rem; }
.logo-row .brand-text { color: #6b7280; }
.logo-row .brand-digit { color: var(--p-primary-800, #1D3B52); }
</style>
