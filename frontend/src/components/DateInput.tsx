import React, { useEffect, useState } from 'react'
import { formatDate, parseDateToISO } from '@/utils/utils'

type DateInputProps = {
  value?: string | null
  onChange: (isoValue: string) => void
  className?: string
  placeholder?: string
  id?: string
  required?: boolean
}

export default function DateInput({ value, onChange, className = '', placeholder = '', id, required }: DateInputProps) {
  const [display, setDisplay] = useState<string>(formatDate(value))

  useEffect(() => {
    setDisplay(formatDate(value))
  }, [value])

  const mask = (v: string) => {
    const numbers = v.replace(/\D/g, '').slice(0, 8)
    if (numbers.length <= 2) return numbers
    if (numbers.length <= 4) return `${numbers.slice(0, 2)}/${numbers.slice(2)}`
    return `${numbers.slice(0, 2)}/${numbers.slice(2, 4)}/${numbers.slice(4, 8)}`
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const next = mask(e.target.value)
    setDisplay(next)

    if (next === '') {
      onChange('')
      return
    }

    if (/^\d{2}\/\d{2}\/\d{4}$/.test(next)) {
      const iso = parseDateToISO(next)
      onChange(iso || '')
    }
  }

  return (
    <input
      id={id}
      type="text"
      inputMode="numeric"
      pattern="\d{2}/\d{2}/\d{4}"
      placeholder={placeholder || 'dd/MM/yyyy'}
      value={display}
      onChange={handleChange}
      className={className}
      required={required}
    />
  )
}
