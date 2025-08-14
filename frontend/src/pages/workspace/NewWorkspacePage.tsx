import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useCreateWorkspace } from '@/features/workspace/hooks'
import { slugify } from '@/lib/utils'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  slug: z
    .string()
    .min(2, 'Slug must be at least 2 characters')
    .max(255)
    .regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, 'Lowercase letters, numbers, and hyphens only'),
  description: z.string().max(1000).optional(),
})

type FormValues = z.infer<typeof schema>

export function NewWorkspacePage() {
  const create = useCreateWorkspace()
  const navigate = useNavigate()
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const nameValue = watch('name')
  useEffect(() => {
    if (nameValue) setValue('slug', slugify(nameValue))
  }, [nameValue, setValue])

  return (
    <div className="mx-auto max-w-lg p-8">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Create workspace</h1>
        <p className="mt-1 text-sm text-gray-500">
          A workspace groups your documents and chat sessions.
        </p>
      </div>

      <Card>
        <CardContent>
          <form
            onSubmit={handleSubmit((d) => create.mutate(d))}
            className="flex flex-col gap-4"
          >
            <Input
              label="Workspace name"
              placeholder="Acme Corp"
              error={errors.name?.message}
              {...register('name')}
            />
            <Input
              label="Slug"
              placeholder="acme-corp"
              hint="Used in URLs — lowercase letters, numbers, hyphens"
              error={errors.slug?.message}
              {...register('slug')}
            />
            <Input
              label="Description (optional)"
              placeholder="What is this workspace for?"
              error={errors.description?.message}
              {...register('description')}
            />
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate(-1)}
              >
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Create workspace
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
