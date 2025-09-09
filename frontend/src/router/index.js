import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import RegistrationView from '../views/RegistrationView.vue'
import PasswordResetRequestView from '../views/PasswordResetRequestView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import CasesView from '../views/CasesView.vue'
import RegistrationPendingView from '../views/RegistrationPendingView.vue'
import TeamsView from '../views/TeamsView.vue'

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
    // Case editor routing: /cases/:caseNumber and optional :tab (default to intake)
    { path: '/cases/:caseNumber', redirect: (to) => ({ name: 'case-detail', params: { caseNumber: to.params.caseNumber, tab: 'core', subtab: 'intake' } }) },
    { path: '/cases/:caseNumber/:tab/:subtab?', name: 'case-detail', component: () => import('../views/CaseView.vue'), props: true },
    { path: '/messages', name: 'messages', component: () => import('../views/MessagesView.vue') },
    { path: '/contacts', name: 'contacts', component: () => import('../views/ContactsView.vue') },
    { path: '/tasks', name: 'tasks', component: () => import('../views/TasksView.vue') },
    { path: '/rfis', name: 'rfis', component: () => import('../views/RfisView.vue') },
    { path: '/ops-plans', name: 'ops-plans', component: () => import('../views/OpsPlansView.vue') },
    { path: '/teams', name: 'teams', component: TeamsView },
    { path: '/reports', name: 'reports', component: () => import('../views/ReportsView.vue') },
    { path: '/events', name: 'events', component: () => import('../views/EventsView.vue') },
    { path: '/admin', name: 'admin', component: () => import('../views/AdminView.vue') },
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
        const wantsCase = typeof to?.path === 'string' && to.path.startsWith('/cases')
        const message = wantsCase ? 'Please log in to view that case.' : 'Please log in to view that page.'
        return { name: 'login', query: { redirect: to.fullPath, message } }
    }
})

export default router