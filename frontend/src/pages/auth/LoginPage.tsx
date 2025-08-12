import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useLogin } from '@/features/auth/hooks'

const schema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
})

type FormValues = z.infer<typeof schema>

export function LoginPage() {
  const login = useLogin()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  return (
    <Card>
      <CardContent>
        <h2 className="mb-6 text-center text-xl font-semibold text-gray-900">
          Sign in to your account
        </h2>
        <form onSubmit={handleSubmit((d) => login.mutate(d))} className="flex flex-col gap-4">
          <Input
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register('email')}
          />
          <Input
            label="Password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            error={errors.password?.message}
            {...register('password')}
          />
          <div className="flex justify-end">
            <Link
              to="/forgot-password"
              className="text-xs text-primary-600 hover:underline"
            >
              Forgot password?
            </Link>
          </div>
          <Button type="submit" loading={login.isPending} className="w-full">
            Sign in
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
          Don't have an account?{' '}
          <Link to="/register" className="font-medium text-primary-600 hover:underline">
            Sign up
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
