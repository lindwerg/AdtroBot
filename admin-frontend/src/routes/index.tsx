import { createBrowserRouter, redirect } from 'react-router'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import UsersPage from '@/pages/Users'
import UserDetailPage from '@/pages/UserDetail'
import PaymentsPage from '@/pages/Payments'
import SubscriptionsPage from '@/pages/Subscriptions'
import TarotSpreadsPage from '@/pages/TarotSpreads'
import MessagesPage from '@/pages/Messages'
import ContentPage from '@/pages/Content'
import PromoCodesPage from '@/pages/PromoCodes'
import ABTestsPage from '@/pages/ABTests'
import MonitoringPage from '@/pages/Monitoring'

// Check localStorage directly (sync) instead of waiting for zustand hydration
function getTokenFromStorage(): string | null {
  try {
    const stored = localStorage.getItem('admin-auth')
    if (!stored) return null
    const parsed = JSON.parse(stored)
    return parsed?.state?.token || null
  } catch {
    return null
  }
}

// Auth check loader
async function requireAuth() {
  const token = getTokenFromStorage()
  if (!token) {
    throw redirect('/login')
  }
  return null
}

// Redirect if already logged in
async function redirectIfAuth() {
  const token = getTokenFromStorage()
  if (token) {
    throw redirect('/')
  }
  return null
}

export const router = createBrowserRouter(
  [
    {
      path: '/login',
      element: <LoginPage />,
      loader: redirectIfAuth,
    },
    {
      path: '/',
      element: <Layout />,
      loader: requireAuth,
      children: [
        { index: true, element: <Dashboard /> },
        { path: 'users', element: <UsersPage /> },
        { path: 'users/:id', element: <UserDetailPage /> },
        { path: 'subscriptions', element: <SubscriptionsPage /> },
        { path: 'payments', element: <PaymentsPage /> },
        { path: 'tarot-spreads', element: <TarotSpreadsPage /> },
        { path: 'messages', element: <MessagesPage /> },
        { path: 'content', element: <ContentPage /> },
        { path: 'promo-codes', element: <PromoCodesPage /> },
        { path: 'ab-tests', element: <ABTestsPage /> },
        { path: 'monitoring', element: <MonitoringPage /> },
      ],
    },
  ],
  {
    basename: '/admin',
  },
)
