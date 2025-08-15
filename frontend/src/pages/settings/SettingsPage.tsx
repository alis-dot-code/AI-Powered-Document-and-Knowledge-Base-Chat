import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/features/auth/store'
import { authApi } from '@/features/auth/api'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'

const profileSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(255),
  avatar_url: z.string().url('Must be a valid URL').optional().or(z.literal('')),
})

type ProfileForm = z.infer<typeof profileSchema>

export function SettingsPage() {
  const user = useAuthStore((s) => s.user)
  const setUser = useAuthStore((s) => s.setUser)
  const qc = useQueryClient()

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: '', avatar_url: '' },
  })

  useEffect(() => {
    if (user) {
      reset({ full_name: user.full_name, avatar_url: user.avatar_url ?? '' })
    }
  }, [user, reset])

  const updateProfile = useMutation({
    mutationFn: (data: ProfileForm) =>
      authApi.updateProfile({
        full_name: data.full_name,
        avatar_url: data.avatar_url || undefined,
      }),
    onSuccess: ({ data }) => {
      setUser(data)
      qc.invalidateQueries({ queryKey: ['auth', 'me'] })
      toast.success('Profile updated')
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail ?? 'Update failed')
    },
  })

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-lg space-y-8">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
          <p className="mt-1 text-sm text-gray-500">Manage your account preferences.</p>
        </div>

        {/* Profile card */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Profile</h2>

          {/* Avatar preview */}
          <div className="mb-5 flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary-100 text-lg font-bold text-primary-700">
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt="avatar"
                  className="h-full w-full rounded-full object-cover"
                />
              ) : (
                user?.full_name?.charAt(0).toUpperCase() ?? '?'
              )}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
          </div>

          <form onSubmit={handleSubmit((d) => updateProfile.mutate(d))} className="space-y-4">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Full Name
              </label>
              <Input {...register('full_name')} placeholder="Your name" />
              {errors.full_name && (
                <p className="mt-1 text-xs text-red-500">{errors.full_name.message}</p>
              )}
            </div>

            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Avatar URL <span className="text-gray-400">(optional)</span>
              </label>
              <Input {...register('avatar_url')} placeholder="https://..." />
              {errors.avatar_url && (
                <p className="mt-1 text-xs text-red-500">{errors.avatar_url.message}</p>
              )}
            </div>

            <div className="pt-1">
              <Button
                type="submit"
                disabled={!isDirty || updateProfile.isPending}
                isLoading={updateProfile.isPending}
              >
                Save Changes
              </Button>
            </div>
          </form>
        </div>

        {/* Account info */}
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="mb-4 text-sm font-semibold text-gray-900">Account</h2>
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Email</dt>
              <dd className="font-medium text-gray-900">{user?.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Email verified</dt>
              <dd className={user?.email_verified ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                {user?.email_verified ? 'Verified' : 'Not verified'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Member since</dt>
              <dd className="text-gray-700">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : '—'}
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
