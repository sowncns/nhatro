import React from 'react'

type DateInputProps = {
  value?: string | null
  onChange: (isoValue: string) => void
  className?: string
  placeholder?: string
  id?: string
  required?: boolean
}

/**
 * DateInput sử dụng native <input type="date">
 * - value: ISO format yyyy-MM-dd (ví dụ "2026-05-23")
 * - onChange: trả về ISO format yyyy-MM-dd
 * - Trình duyệt tự hiển thị theo locale của user (VN = dd/MM/yyyy) + date picker
 */
export default function DateInput({ value, onChange, className = '', id, required }: DateInputProps) {
  // Ensure value is valid ISO date or empty
  const safeValue = value && /^\d{4}-\d{2}-\d{2}/.test(value)
    ? value.substring(0, 10)
    : ''

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value) // native date input always returns yyyy-MM-dd
  }

  return (
    <input
      id={id}
      type="date"
      value={safeValue}
      onChange={handleChange}
      className={className}
      required={required}
    />
  )
}
