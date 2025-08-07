import { useRef, useState, type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { useClickOutside } from '@/hooks/useClickOutside'

interface DropdownItem {
  label: string
  onClick: () => void
  danger?: boolean
  icon?: ReactNode
}

interface DropdownProps {
  trigger: ReactNode
  items: DropdownItem[]
  align?: 'left' | 'right'
}

export function Dropdown({ trigger, items, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useClickOutside(ref, () => setOpen(false))

  return (
    <div ref={ref} className="relative inline-block">
      <div onClick={() => setOpen((o) => !o)} className="cursor-pointer">
        {trigger}
      </div>
      {open && (
        <div
          className={cn(
            'absolute z-20 mt-1 min-w-[160px] rounded-lg border border-gray-200 bg-white py-1 shadow-lg',
            align === 'right' ? 'right-0' : 'left-0'
          )}
        >
          {items.map((item, i) => (
            <button
              key={i}
              onClick={() => {
                item.onClick()
                setOpen(false)
              }}
              className={cn(
                'flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors',
                item.danger
                  ? 'text-red-600 hover:bg-red-50'
                  : 'text-gray-700 hover:bg-gray-50'
              )}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
