import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useForgotPassword } from '@/features/auth/hooks'
import { CheckCircle } from 'lucide-react'

const schema = z.object({ email: z.string().email('Enter a valid email') })
type FormValues = z.infer<typeof schema>

export function ForgotPasswordPage() {
  const forgot = useForgotPassword()
  const [sent, setSent] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  if (sent) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 text-center">
          <CheckCircle className="h-10 w-10 text-green-500" />
          <h2 className="text-lg font-semibold text-gray-900">Check your email</h2>
          <p className="text-sm text-gray-500">
            We sent a password reset link. Check your inbox.
          </p>
          <Link to="/login" className="text-sm font-medium text-primary-600 hover:underline">
            Back to sign in
          </Link>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent>
        <h2 className="mb-2 text-center text-xl font-semibold text-gray-900">
          Forgot password?
        </h2>
        <p className="mb-6 text-center text-sm text-gray-500">
          Enter your email and we'll send you a reset link.
        </p>
        <form
          onSubmit={handleSubmit((d) =>
            forgot.mutate(d, { onSuccess: () => setSent(true) })
          )}
          className="flex flex-col gap-4"
        >
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register('email')}
          />
          <Button type="submit" loading={forgot.isPending} className="w-full">
            Send reset link
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-500">
          <Link to="/login" className="font-medium text-primary-600 hover:underline">
            Back to sign in
          </Link>
        </p>
      </CardContent>
    </Card>
  )
}
