import { createBrowserRouter, redirect } from 'react-router'
import { useAuthStore } from '@/store/auth'
import Layout from '@/components/Layout'
import LoginPage from '@/pages/Login'
import Dashboard from '@/pages/Dashboard'
import UsersPage from '@/pages/Users'

// Auth check loader
async function requireAuth() {
  const isAuthenticated = useAuthStore.getState().isAuthenticated()
  if (!isAuthenticated) {
    throw redirect('/login')
  }
  return null
}

// Redirect if already logged in
async function redirectIfAuth() {
  const isAuthenticated = useAuthStore.getState().isAuthenticated()
  if (isAuthenticated) {
    throw redirect('/')
  }
  return null
}

export const router = createBrowserRouter([
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
      { path: 'users/:id', element: <div>User Detail (Coming soon)</div> },
      { path: 'subscriptions', element: <div>Subscriptions (Coming soon)</div> },
      { path: 'payments', element: <div>Payments (Coming soon)</div> },
      { path: 'messages', element: <div>Messages (Coming soon)</div> },
      { path: 'promo-codes', element: <div>Promo Codes (Coming soon)</div> },
      { path: 'ab-tests', element: <div>A/B Tests (Coming soon)</div> },
    ],
  },
])
