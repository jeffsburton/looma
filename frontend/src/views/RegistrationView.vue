<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import InputMask from 'primevue/inputmask'
import Password from 'primevue/password'
import Button from 'primevue/button'
import FloatLabel from 'primevue/floatlabel'
import api from '../lib/api'

const router = useRouter()
const toast = useToast()
const loading = ref(false)

const form = ref({
  firstName: '',
  lastName: '',
  email: '',
  phoneNumber: '',
  organization: '',
  referredBy: '',
  telegram: '',
  password: '',
  confirmPassword: ''
})

const errors = ref({})

const validateForm = () => {
  errors.value = {}

  if (!form.value.firstName.trim()) {
    errors.value.firstName = 'First name is required'
  }

  if (!form.value.lastName.trim()) {
    errors.value.lastName = 'Last name is required'
  }

  if (!form.value.email) {
    errors.value.email = 'Email is required'
  } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
    errors.value.email = 'Please enter a valid email'
  }

  if (!form.value.phoneNumber || form.value.phoneNumber.replace(/\D/g, '').length < 10) {
    errors.value.phoneNumber = 'Phone number is required and must be 10 digits'
  }

  if (!form.value.organization.trim()) {
    errors.value.organization = 'Organization is required'
  }

  if (!form.value.referredBy.trim()) {
    errors.value.referredBy = 'Referred by is required'
  }

  if (!form.value.password) {
    errors.value.password = 'Password is required'
  } else {
    const password = form.value.password
    const passwordErrors = []

    if (password.length < 8) {
      passwordErrors.push('at least 8 characters')
    }

    if (!/(?=.*[0-9])/.test(password)) {
      passwordErrors.push('at least one number')
    }

    if (!/(?=.*[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?])/.test(password)) {
      passwordErrors.push('at least one special character')
    }

    if (!/(?=.*[a-z])/.test(password)) {
      passwordErrors.push('at least one lowercase letter')
    }

    if (!/(?=.*[A-Z])/.test(password)) {
      passwordErrors.push('at least one uppercase letter')
    }

    if (passwordErrors.length > 0) {
      errors.value.password = `Password must contain ${passwordErrors.join(', ')}`
    }
  }

  if (form.value.password !== form.value.confirmPassword) {
    errors.value.confirmPassword = 'Passwords do not match'
  }

  return Object.keys(errors.value).length === 0
}

const handleRegistration = async () => {
  if (!validateForm()) return

  loading.value = true
  try {
    // Prepare payload mapping to backend schema
    const phoneDigits = (form.value.phoneNumber || '').replace(/\D/g, '')
    const payload = {
      first_name: form.value.firstName.trim(),
      last_name: form.value.lastName.trim(),
      email: form.value.email.trim(),
      password: form.value.password,
      phone: phoneDigits || form.value.phoneNumber || null,
      organization: form.value.organization.trim(),
      referred_by: form.value.referredBy.trim(),
      telegram: (form.value.telegram || '').trim() || null,
    }

    const response = await api.post('/api/v1/auth/register', payload)

    // Expect 201 Created with UserRead; success path
    toast.add({
      severity: 'success',
      summary: 'Registration Successful',
      detail: 'Your account has been created successfully',
      life: 3000
    })

    router.push({ name: 'registration-pending' })
  } catch (error) {
    console.error('Registration failed:', error)

    // Attempt to map server errors to field errors and toast
    if (error?.response) {
      const status = error.response.status
      const data = error.response.data

      if (status === 400 && typeof data?.detail === 'string') {
        // Duplicate email or similar business error
        errors.value.email = data.detail
        toast.add({ severity: 'error', summary: 'Registration Failed', detail: data.detail, life: 4000 })
      } else if (status === 422 && Array.isArray(data?.detail)) {
        // FastAPI validation errors
        for (const err of data.detail) {
          const loc = err?.loc || []
          const field = loc[loc.length - 1]
          const msg = err?.msg || 'Invalid value'
          // Map backend field names to our form fields
          switch (field) {
            case 'first_name':
              errors.value.firstName = msg; break
            case 'last_name':
              errors.value.lastName = msg; break
            case 'email':
              errors.value.email = msg; break
            case 'password':
              errors.value.password = msg; break
            case 'phone':
              errors.value.phoneNumber = msg; break
            case 'organization':
              errors.value.organization = msg; break
            case 'referred_by':
              errors.value.referredBy = msg; break
            case 'telegram':
              errors.value.telegram = msg; break
            default:
              // Unmapped field; show a general message
              break
          }
        }
        toast.add({ severity: 'error', summary: 'Validation Error', detail: 'Please review the highlighted fields.', life: 4000 })
      } else {
        const detail = typeof data?.detail === 'string' && data.detail.length ? data.detail : 'Please try again later.'
        toast.add({ severity: 'error', summary: 'Registration Failed', detail, life: 4000 })
      }
    } else {
      toast.add({ severity: 'error', summary: 'Registration Failed', detail: 'Network error. Please try again.', life: 4000 })
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex align-items-center justify-content-center min-h-screen p-4 surface-50">
    <Card class="w-full max-w-2xl shadow-4">
      <template #title>
        <div class="text-center text-3xl font-bold text-900">Create Account</div>
        <div class="text-center text-600 text-base mt-2 mb-4">
          You should register to use the site if you have been asked to by Called2Rescue leadership.
          Otherwise, please do not create an account.
        </div>
      </template>

      <template #content>
        <form @submit.prevent="handleRegistration" class="flex flex-column gap-4">

          <!-- Name Fields Row -->
          <div class="grid">
            <div class="col-12 md:col-6">
              <div class="flex flex-column gap-2">
                <FloatLabel>
                  <InputText
                      id="firstName"
                      v-model="form.firstName"
                      class="w-full"
                      :class="{ 'p-invalid': errors.firstName }"
                  />
                  <label for="firstName">First Name *</label>
                </FloatLabel>
                <small v-if="errors.firstName" class="p-error">{{ errors.firstName }}</small>
              </div>
            </div>

            <div class="col-12 md:col-6">
              <div class="flex flex-column gap-2">
                <FloatLabel>
                  <InputText
                      id="lastName"
                      v-model="form.lastName"
                      class="w-full"
                      :class="{ 'p-invalid': errors.lastName }"
                  />
                  <label for="lastName">Last Name *</label>
                </FloatLabel>
                <small v-if="errors.lastName" class="p-error">{{ errors.lastName }}</small>
              </div>
            </div>
          </div>

          <!-- Email Field -->
          <div class="flex flex-column gap-2">
            <FloatLabel>
              <InputText
                  id="email"
                  v-model="form.email"
                  type="email"
                  class="w-full"
                  :class="{ 'p-invalid': errors.email }"
              />
              <label for="email">Email Address *</label>
            </FloatLabel>
            <small v-if="errors.email" class="p-error">{{ errors.email }}</small>
          </div>

          <!-- Phone Number Field with Mask -->
          <div class="flex flex-column gap-2">
            <FloatLabel>
              <InputMask
                  id="phoneNumber"
                  v-model="form.phoneNumber"
                  mask="999-999-9999"
                  class="w-full"
                  :class="{ 'p-invalid': errors.phoneNumber }"
                  placeholder="123-456-7890"
              />
              <label for="phoneNumber">Phone Number *</label>
            </FloatLabel>
            <small v-if="errors.phoneNumber" class="p-error">{{ errors.phoneNumber }}</small>
          </div>

          <!-- Organization Field -->
          <div class="flex flex-column gap-2">
            <FloatLabel>
              <InputText
                  id="organization"
                  v-model="form.organization"
                  class="w-full"
                  :class="{ 'p-invalid': errors.organization }"
              />
              <label for="organization">Organization *</label>
            </FloatLabel>
            <small v-if="errors.organization" class="p-error">{{ errors.organization }}</small>
          </div>

          <!-- Referred By Field (Now Required) -->
          <div class="flex flex-column gap-2">
            <FloatLabel>
              <InputText
                  id="referredBy"
                  v-model="form.referredBy"
                  class="w-full"
                  :class="{ 'p-invalid': errors.referredBy }"
              />
              <label for="referredBy">Referred By *</label>
            </FloatLabel>
            <small v-if="errors.referredBy" class="p-error">{{ errors.referredBy }}</small>
          </div>

          <!-- Telegram Handle (optional) -->
          <div class="flex flex-column gap-2">
            <FloatLabel>
              <InputText
                  id="telegram"
                  v-model="form.telegram"
                  class="w-full"
                  :class="{ 'p-invalid': errors.telegram }"
                  placeholder="@yourhandle"
              />
              <label for="telegram">Telegram Handle</label>
            </FloatLabel>
            <small v-if="errors.telegram" class="p-error">{{ errors.telegram }}</small>
          </div>
          <!-- Password Fields Row -->
          <div class="grid">
            <div class="col-12 md:col-6">
              <div class="flex flex-column gap-2">
                <FloatLabel>
                  <Password
                      id="password"
                      v-model="form.password"
                      class="w-full"
                      :class="{ 'p-invalid': errors.password }"
                      :feedback="true"
                      toggleMask
                  />
                  <label for="password">Password *</label>
                </FloatLabel>
                <small v-if="errors.password" class="p-error">{{ errors.password }}</small>
                <small v-else class="text-500 text-sm">
                  Must contain: 8+ characters, one number, one special character, one uppercase and one lowercase letter
                </small>
              </div>
            </div>

            <div class="col-12 md:col-6">
              <div class="flex flex-column gap-2">
                <FloatLabel>
                  <Password
                      id="confirmPassword"
                      v-model="form.confirmPassword"
                      class="w-full"
                      :class="{ 'p-invalid': errors.confirmPassword }"
                      :feedback="false"
                      toggleMask
                  />
                  <label for="confirmPassword">Confirm Password *</label>
                </FloatLabel>
                <small v-if="errors.confirmPassword" class="p-error">{{ errors.confirmPassword }}</small>
              </div>
            </div>
          </div>

          <!-- Submit Button -->
          <Button
              type="submit"
              label="Create Account"
              class="w-full mt-4"
              size="large"
              :loading="loading"
          />
        </form>

        <!-- Sign in link -->
        <div class="text-center mt-6 pt-4 border-top-1 surface-border">
          <span class="text-600">Already have an account? </span>
          <router-link to="/login" class="text-primary font-medium no-underline hover:underline">
            Sign in here
          </router-link>
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
/* Ensure password components take full width */
:deep(.p-password) {
  width: 100%;
}

:deep(.p-password .p-inputtext) {
  width: 100%;
}
</style>