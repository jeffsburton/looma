import { createApp } from 'vue'
import App from './App.vue'

import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
import './assets/theme.css'

import './assets/override.css'

import ToastService from 'primevue/toastservice'
import Tooltip from 'primevue/tooltip'
import router from './router'
import { installGlobalFetch } from './lib/fetchWrapper'

if (import.meta.env.DEV) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  window.__LOOMA_API_URL = 'http://localhost:8000'
    console.log("backend URL (you shouldn't see this in production!): ", window.__LOOMA_API_URL)
} else {
  // Keep production unified origin behavior
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete window.__LOOMA_API_URL
}


// Ensure all fetch() calls go through our axios api wrapper and interceptors
installGlobalFetch()

const app = createApp(App)

// Custom darker red theme
const customAura = {
    ...Aura,
    semantic: {
        ...Aura.semantic,
        primary: {
            50: '#F2F7FA',
            100: '#E6EFF6',
            200: '#C9DFEE',
            300: '#A7CBE3',
            400: '#82B3D5',
            500: '#39729B',
            600: '#316285',
            700: '#274E6B',
            800: '#1D3B52',
            900: '#142838',
            950: '#0D1A25'
        }
    }
}

app.use(PrimeVue, {
    theme: {
        preset: customAura,
        options: {
            darkModeSelector: false
        }
    }
})
app.use(ToastService)
app.use(router)
app.directive('tooltip', Tooltip)

app.mount('#app')