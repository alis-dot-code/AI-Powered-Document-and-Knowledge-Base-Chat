import api from '@/lib/axios'
import type { User } from '@/types'
import type {
  LoginRequest,
  RegisterRequest,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  UpdateProfileRequest,
} from './types'

export const authApi = {
  register: (data: RegisterRequest) =>
    api.post<{ user: User }>('/auth/register', data),

  login: (data: LoginRequest) =>
    api.post<{ user: User }>('/auth/login', data),

  logout: () => api.post('/auth/logout'),

  refresh: () => api.post('/auth/refresh'),

  forgotPassword: (data: ForgotPasswordRequest) =>
    api.post('/auth/forgot-password', data),

  resetPassword: (data: ResetPasswordRequest) =>
    api.post('/auth/reset-password', data),

  me: () => api.get<User>('/auth/me'),

  updateProfile: (data: UpdateProfileRequest) =>
    api.patch<User>('/auth/me', data),
}
