import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useScrapeUrl } from '@/features/documents/hooks'

const schema = z.object({
  url: z.string().url('Enter a valid URL'),
  title: z.string().max(512).optional(),
})

type FormValues = z.infer<typeof schema>

interface UrlScrapeFormProps {
  workspaceId: string
  onSuccess?: () => void
}

export function UrlScrapeForm({ workspaceId, onSuccess }: UrlScrapeFormProps) {
  const scrape = useScrapeUrl(workspaceId)
  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (values: FormValues) => {
    scrape.mutate(values, {
      onSuccess: () => {
        reset()
        onSuccess?.()
      },
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3">
      <Input
        label="URL"
        type="url"
        placeholder="https://docs.example.com/page"
        error={errors.url?.message}
        {...register('url')}
      />
      <Input
        label="Title (optional)"
        placeholder="My Web Page"
        error={errors.title?.message}
        {...register('title')}
      />
      <Button type="submit" loading={scrape.isPending}>
        Scrape URL
      </Button>
    </form>
  )
}
