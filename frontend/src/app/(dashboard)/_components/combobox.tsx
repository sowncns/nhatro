'use client'

import { useState, useRef, useEffect } from 'react'
import { Check, ChevronsUpDown, Search } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface Option {
  value: string
  label: string
  description?: string
  image?: string
}

interface ComboboxProps {
  options: Option[]
  value: string
  onChange: (value: string) => void
  placeholder?: string
  emptyText?: string
  className?: string
}

export function Combobox({
  options,
  value,
  onChange,
  placeholder = "Chọn một tùy chọn...",
  emptyText = "Không tìm thấy kết quả.",
  className
}: ComboboxProps) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState("")
  const containerRef = useRef<HTMLDivElement>(null)

  const selectedOption = options.find((opt) => opt.value === value)

  const filteredOptions = options.filter((opt) =>
    opt.label.toLowerCase().includes(search.toLowerCase()) ||
    opt.value.toLowerCase().includes(search.toLowerCase()) ||
    opt.description?.toLowerCase().includes(search.toLowerCase())
  )

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <div className={cn("relative w-full", className)} ref={containerRef}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex h-10 w-full items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/15 dark:border-slate-800 dark:bg-slate-950"
      >
        <span className="flex items-center gap-2 truncate">
          {selectedOption?.image && (
            <img src={selectedOption.image} alt="" className="h-5 w-5 object-contain" />
          )}
          {selectedOption ? selectedOption.label : <span className="text-slate-400">{placeholder}</span>}
        </span>
        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
      </button>

      {open && (
        <div className="absolute z-50 mt-1 max-h-60 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg animate-in fade-in zoom-in-95 dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center border-b border-slate-100 px-3 dark:border-slate-800">
            <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
            <input
              className="flex h-10 w-full bg-transparent py-3 text-sm outline-none placeholder:text-slate-400"
              placeholder="Tìm kiếm..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto p-1">
            {filteredOptions.length === 0 ? (
              <div className="py-6 text-center text-sm text-slate-500">{emptyText}</div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    onChange(option.value)
                    setOpen(false)
                    setSearch("")
                  }}
                  className={cn(
                    "relative flex w-full cursor-default select-none items-center rounded-lg px-2 py-2 text-sm outline-none transition-colors hover:bg-slate-100 dark:hover:bg-slate-800",
                    value === option.value && "bg-slate-50 dark:bg-slate-800/50"
                  )}
                >
                  <div className="flex flex-1 items-center gap-3">
                    {option.image && (
                      <img src={option.image} alt="" className="h-6 w-6 object-contain" />
                    )}
                    <div className="flex flex-col items-start">
                      <span className="font-medium">{option.label}</span>
                      {option.description && (
                        <span className="text-[10px] text-slate-400 line-clamp-1">{option.description}</span>
                      )}
                    </div>
                  </div>
                  {value === option.value && (
                    <Check className="ml-auto h-4 w-4 text-emerald-500" />
                  )}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
