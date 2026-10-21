import { create } from 'zustand'
import api from '../lib/api'

const useAuthStore = create((set) => ({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || null,
  loading: false,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      set({ user: data.user, token: data.access_token, loading: false })
      return true
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.detail || 'Login failed'
      set({ error: msg, loading: false })
      return false
    }
  },

  register: async (email, password) => {
    set({ loading: true, error: null })
    try {
      await api.post('/auth/register', { email, password })
      set({ loading: false })
      return true
    } catch (err) {
      const msg = err.response?.data?.detail?.message || err.response?.data?.detail || 'Registration failed'
      set({ error: msg, loading: false })
      return false
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null })
  },

  clearError: () => set({ error: null }),
}))

export default useAuthStore
