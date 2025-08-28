<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FloatLabel from 'primevue/floatlabel'
import Checkbox from 'primevue/checkbox'
import api from '../lib/api'
import { setCookie } from '../lib/cookies'
import { setPermissions } from '../lib/permissions'

const router = useRouter()
const route = useRoute()
const toast = useToast()

const loading = ref(false)
const rememberMe = ref(false)

const form = ref({
  email: '',
  password: ''
})

const errors = ref({})
const loginError = ref('')

const validateForm = () => {
  errors.value = {}

  if (!form.value.email) {
    errors.value.email = 'Email is required'
  }

  if (!form.value.password) {
    errors.value.password = 'Password is required'
  }

  return Object.keys(errors.value).length === 0
}

const handleLogin = async () => {
  loginError.value = ''
  if (!validateForm()) return

  loading.value = true
  try {
    // Call backend login API
    const response = await api.post('/api/v1/auth/login', {
      email: form.value.email,
      password: form.value.password,
    })

    const { access_token, codes } = response.data || {}
    if (!access_token) {
      throw new Error('No access token received')
    }

    // Persist token in secure cookie and basic user info
    // Remember me: 30 days; otherwise session cookie
    const maxAge = rememberMe.value ? 60 * 60 * 24 * 30 : undefined
    const secure = window.location.protocol === 'https:'
    setCookie('access_token', access_token, { maxAge, path: '/', sameSite: 'Strict', secure })
    localStorage.setItem('user_email', form.value.email)
    // Mark client as authenticated (fallback for HttpOnly cookie flows)
    localStorage.setItem('is_authenticated', '1')

    // Cache permission codes for UI gating
    try { setPermissions(Array.isArray(codes) ? codes : []) } catch (_) { /* noop */ }

    toast.add({
      severity: 'success',
      summary: 'Login Successful',
      detail: 'Welcome back!',
      life: 3000
    })

    // Redirect to intended page or home
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    console.error('Login failed:', error)
    let detail = 'Invalid credentials. Please try again.'
    if (error?.response) {
      const status = error.response.status
      const msg = error.response.data?.detail
      if (status === 401 && typeof msg === 'string' && msg.length) {
        detail = msg
      } else if (typeof msg === 'string' && msg.length) {
        detail = msg
      }
    }
    loginError.value = detail
    toast.add({
      severity: 'error',
      summary: 'Login Failed',
      detail,
      life: 4000
    })
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Show message if redirected with a message
  if (route.query.message) {
    toast.add({
      severity: 'info',
      summary: 'Info',
      detail: route.query.message,
      life: 5000
    })
  }
})
</script>

<template>
  <!-- Full viewport with no margins/padding and surface background -->
  <div class="auth-page flex align-items-center justify-content-center surface-50">
    <div class="px-6 w-full flex justify-content-center">
      <!-- Container for both cards -->
      <div class="w-full max-w-lg flex flex-column gap-4">

        <!-- Branding/Info Card - Horizontal Layout -->
        <Card class="w-full shadow-3">
          <template #content>
            <div class="flex align-items-center gap-4 py-3">
              <!-- Logo on the left -->
              <div class="flex-shrink-0">
                <img
                    src="/images/shepherds-bug.png"
                    alt="Company Logo"
                    class="h-6rem"
                    style="max-width: 120px; object-fit: contain;"
                />
              </div>

              <!-- Text content on the right -->
              <div class="flex-grow-1">
                <!-- Company/Site Name -->
                <h1 class="text-2xl font-bold text-900 mb-2 m-0">
                  Called2Rescue
                </h1>

                <!-- Tagline -->
                <p class="text-base text-600 mb-2 m-0">
                  Search for the Missing & Rescue the Lost
                </p>

                <!-- Brief description -->
                <p class="text-sm text-500 line-height-3 m-0">
                  This site is for the use of <a href="https://called2rescue.com" target="_blank" class="text-primary no-underline hover:underline">Called2Rescue</a> personnel and partner organizations. Any other use is prohibited.
                </p>
              </div>
            </div>
          </template>
        </Card>

        <!-- Login Card -->
        <Card class="w-full shadow-4">
          <template #title>
            <div class="text-center text-3xl font-bold text-900 mb-2">
              Sign In
            </div>
            <div class="text-center text-600 text-base mb-0">
              Welcome back! Please sign in to your account.
            </div>
          </template>

          <template #content>
            <!-- Inline error for login failures -->
            <div v-if="loginError" class="p-error text-center mb-3">{{ loginError }}</div>
            <!-- Form with proper spacing -->
            <form @submit.prevent="handleLogin" class="flex flex-column gap-5">

              <!-- Email Field -->
              <div class="flex flex-column gap-2">
                <FloatLabel>
                  <InputText
                      id="email"
                      v-model="form.email"
                      type="email"
                      class="w-full"
                      :class="{ 'p-invalid': errors.email }"
                      size="large"
                  />
                  <label for="email" class="text-900 font-medium">Email</label>
                </FloatLabel>
                <small v-if="errors.email" class="p-error">{{ errors.email }}</small>
              </div>

              <!-- Password Field with explicit width fix -->
              <div class="flex flex-column gap-2">
                <FloatLabel>
                  <Password
                      id="password"
                      v-model="form.password"
                      inputClass="w-full"
                      class="w-full"
                      :class="{ 'p-invalid': errors.password }"
                      :feedback="false"
                      toggleMask
                      size="large"
                  />
                  <label for="password" class="text-900 font-medium">Password</label>
                </FloatLabel>
                <small v-if="errors.password" class="p-error">{{ errors.password }}</small>
              </div>

              <!-- Remember Me (centered) - Best approach -->
              <div class="flex align-items-center justify-content-center mt-2">
                <div class="flex align-items-center gap-2">
                  <Checkbox
                      id="rememberMe"
                      v-model="rememberMe"
                      :binary="true"
                  />
                  <label for="rememberMe" class="text-900 font-medium cursor-pointer" @click="$event.preventDefault(); rememberMe = !rememberMe">
                    Remember me
                  </label>
                </div>
              </div>

              <!-- Submit Button -->
              <Button
                  type="submit"
                  label="Sign In"
                  class="w-full mt-4"
                  size="large"
                  :loading="loading"
              />
            </form>

            <!-- Links row - Sign up left, Forgot password right -->
            <div class="flex justify-content-between align-items-center mt-6 pt-4 border-top-1 surface-border">
              <div>
                <span class="text-600">Don't have an account? </span>
                <router-link
                    to="/register"
                    class="text-primary font-medium no-underline hover:underline"
                >
                  Sign up here
                </router-link>
              </div>

              <router-link
                  to="/password-reset"
                  class="text-primary font-medium no-underline hover:underline"
              >
                Forgot password?
              </router-link>
            </div>
          </template>
        </Card>

      </div>
    </div>
  </div>
</template>

<style scoped>
/* Ensure password component takes full width */
:deep(.p-password) {
  width: 100%;
}

:deep(.p-password .p-inputtext) {
  width: 100%;
}
</style>