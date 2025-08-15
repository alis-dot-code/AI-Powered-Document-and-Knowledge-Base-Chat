import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authApi } from './api'
import { useAuthStore } from './store'
import type { LoginRequest, RegisterRequest, ForgotPasswordRequest } from './types'

export function useMe() {
  const setUser = useAuthStore((s) => s.setUser)

  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const { data } = await authApi.me()
      setUser(data)
      return data
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
}

export function useLogin() {
  const setUser = useAuthStore((s) => s.setUser)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: LoginRequest) => authApi.login(data),
    onSuccess: ({ data }) => {
      setUser(data.user)
      navigate('/dashboard')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Login failed')
    },
  })
}

export function useRegister() {
  const setUser = useAuthStore((s) => s.setUser)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: (data: RegisterRequest) => authApi.register(data),
    onSuccess: ({ data }) => {
      setUser(data.user)
      navigate('/dashboard')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Registration failed')
    },
  })
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout)
  const qc = useQueryClient()
  const navigate = useNavigate()

  return useMutation({
    mutationFn: () => authApi.logout(),
    onSettled: () => {
      logout()
      qc.clear()
      navigate('/login')
    },
  })
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: (data: ForgotPasswordRequest) => authApi.forgotPassword(data),
    onSuccess: () => {
      toast.success('Password reset email sent')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.error?.message ?? 'Request failed')
    },
  })
}
