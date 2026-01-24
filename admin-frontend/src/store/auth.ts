import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

interface AuthState {
  token: string | null
  _hasHydrated: boolean
  setToken: (token: string | null) => void
  logout: () => void
  isAuthenticated: () => boolean
  setHasHydrated: (state: boolean) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      _hasHydrated: false,
      setToken: (token) => set({ token }),
      logout: () => set({ token: null }),
      isAuthenticated: () => get().token !== null,
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: 'admin-auth',
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true)
      },
    }
  )
)
