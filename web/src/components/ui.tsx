import { useEffect, useId, useRef, type ReactNode } from 'react'
import { allZones } from '../lib/time'

/** A modal built on native <dialog>: focus trapping, Escape to close, and a backdrop for free. */
export function Dialog({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])
  return (
    <dialog
      ref={ref}
      onClose={onClose}
      aria-label={title}
      className="m-auto w-full max-w-xl rounded-xl p-0 shadow-xl backdrop:bg-stone-900/40"
    >
      {open && (
        <div className="max-h-[85vh] overflow-y-auto p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">{title}</h2>
            <button type="button" onClick={onClose} className="text-stone-400 hover:text-stone-700" aria-label="Close">
              ✕
            </button>
          </div>
          {children}
        </div>
      )}
    </dialog>
  )
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-stone-700">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-stone-500">{hint}</span>}
    </label>
  )
}

export const inputClass =
  'w-full rounded-md border border-stone-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-teal-600 focus:ring-1 focus:ring-teal-600 focus:outline-none'

export function Button({
  variant = 'primary',
  className = '',
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }) {
  const styles = {
    primary: 'bg-teal-700 text-white hover:bg-teal-800 disabled:bg-teal-700/50',
    secondary: 'border border-stone-300 bg-white text-stone-700 hover:bg-stone-50',
    danger: 'text-red-700 hover:bg-red-50',
  }[variant]
  return (
    <button
      type="button"
      className={`rounded-md px-3 py-2 text-sm font-medium ${styles} ${className}`}
      {...props}
    />
  )
}

export function ErrorText({ error }: { error: unknown }) {
  if (!error) return null
  return (
    <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
      {error instanceof Error ? error.message : String(error)}
    </p>
  )
}

/** Free-text zone input with every IANA zone as a suggestion (the server validates it). */
export function TimeZoneInput({
  value,
  onChange,
  required,
  placeholder,
}: {
  value: string
  onChange: (zone: string) => void
  required?: boolean
  placeholder?: string
}) {
  const listId = useId()
  return (
    <>
      <input
        className={inputClass}
        list={listId}
        value={value}
        required={required}
        placeholder={placeholder ?? 'e.g. Asia/Tokyo'}
        onChange={(e) => onChange(e.target.value)}
      />
      <datalist id={listId}>
        {allZones().map((zone) => (
          <option key={zone} value={zone} />
        ))}
      </datalist>
    </>
  )
}

const PHASE_STYLES: Record<string, string> = {
  current: 'bg-teal-100 text-teal-800',
  upcoming: 'bg-sky-100 text-sky-800',
  past: 'bg-stone-200 text-stone-700',
  unscheduled: 'bg-amber-100 text-amber-800',
}

export function Badge({ children, tone }: { children: ReactNode; tone?: string }) {
  const style = (tone && PHASE_STYLES[tone]) ?? 'bg-stone-100 text-stone-700'
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${style}`}>{children}</span>
}
