import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegistrationView from '../views/RegistrationView.vue'
import PasswordResetRequestView from '../views/PasswordResetRequestView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import CasesView from '../views/CasesView.vue'
import RegistrationPendingView from '../views/RegistrationPendingView.vue'

const routes = [
    // Public routes (no authentication required)
    { path: '/login', name: 'login', component: LoginView, meta: { public: true } },
    { path: '/register', name: 'register', component: RegistrationView, meta: { public: true } },
    { path: '/password-reset', name: 'password-reset-request', component: PasswordResetRequestView, meta: { public: true } },
    { path: '/reset-password/:token?', name: 'reset-password', component: ResetPasswordView, meta: { public: true }, props: true },
    { path: '/registration/pending', name: 'registration-pending', component: RegistrationPendingView, meta: { public: true } },

    // Protected routes (authentication required)
    { path: '/', redirect: { name: 'cases' } },
    { path: '/cases', name: 'cases', component: CasesView },
    { path: '/case', name: 'case', component: () => import('../views/CaseView.vue') },
    { path: '/messages', name: 'messages', component: () => import('../views/MessagesView.vue') },
    { path: '/contacts', name: 'contacts', component: () => import('../views/ContactsView.vue') },
    { path: '/tasks', name: 'tasks', component: () => import('../views/TasksView.vue') },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

import { getCookie } from '../lib/cookies'

router.beforeEach((to) => {
    // If password reset link contains token query, redirect to reset-password route
    if (to.name === 'password-reset-request' && to.query?.token) {
        return { name: 'reset-password', params: { token: to.query.token } }
    }

    if (to.meta.public) return

    const token = getCookie('access_token')
    const flag = typeof window !== 'undefined' && window.localStorage?.getItem('is_authenticated') === '1'

    if (!token && !flag) {
        return { name: 'login', query: { redirect: to.fullPath } }
    }
})

export default router