import type { ButtonHTMLAttributes, ReactNode } from 'react'

import type { RangeKey } from '../api/types'

export function Card({ title, action, children, className = '' }: {
  title?: ReactNode
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`rounded-xl border border-border bg-surface p-4 sm:p-5 ${className}`}>
      {(title || action) && (
        <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  )
}

export function Stat({ label, value, sub, tone }: {
  label: string
  value: ReactNode
  sub?: ReactNode
  tone?: 'warn' | 'over' | 'good'
}) {
  const toneClass = tone === 'over' ? 'text-over' : tone === 'warn' ? 'text-warn' : tone === 'good' ? 'text-good' : 'text-ink'
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-ink-3">{label}</div>
      <div className={`tabular mt-1 text-2xl font-semibold ${toneClass}`}>{value}</div>
      {sub && <div className="mt-0.5 text-sm text-ink-2">{sub}</div>}
    </div>
  )
}

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'

export function Button({ variant = 'secondary', className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const styles: Record<Variant, string> = {
    primary: 'bg-primary text-primary-ink hover:opacity-90',
    secondary: 'border border-border bg-surface text-ink hover:bg-surface-2',
    ghost: 'text-link hover:bg-surface-2',
    danger: 'border border-border bg-surface text-over hover:bg-over-soft',
  }
  return (
    <button
      type="button"
      {...props}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]} ${className}`}
    />
  )
}

const RANGE_OPTIONS: { key: RangeKey; label: string }[] = [
  { key: '3m', label: '3M' },
  { key: '6m', label: '6M' },
  { key: '1y', label: '1Y' },
  { key: 'ytd', label: 'YTD' },
  { key: 'all', label: 'All' },
]

/** Segmented single-choice control (date ranges, view modes). */
export function Segmented<K extends string>({ value, onChange, options, label }: {
  value: K
  onChange: (k: K) => void
  options: { key: K; label: string }[]
  label: string
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-lg border border-border bg-surface-2 p-0.5">
      {options.map((o) => (
        <button
          key={o.key}
          type="button"
          role="radio"
          aria-checked={value === o.key}
          onClick={() => onChange(o.key)}
          className={`rounded-md px-2.5 py-1 text-sm font-medium transition ${
            value === o.key ? 'bg-primary text-primary-ink shadow-sm' : 'text-ink-2 hover:text-ink'
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function RangePicker({ value, onChange, options = RANGE_OPTIONS }: {
  value: RangeKey
  onChange: (r: RangeKey) => void
  options?: { key: RangeKey; label: string }[]
}) {
  return <Segmented label="Date range" value={value} onChange={onChange} options={options} />
}

export function Switch({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className="inline-flex items-center gap-2 text-sm text-ink-2 hover:text-ink"
    >
      <span className={`relative inline-block h-5 w-9 shrink-0 rounded-full transition ${checked ? 'bg-primary' : 'bg-surface-2 ring-1 ring-border'}`}>
        <span
          className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-all ${checked ? 'left-[1.125rem]' : 'left-0.5'}`}
        />
      </span>
      {label}
    </button>
  )
}

export function Badge({ tone = 'neutral', children }: { tone?: 'neutral' | 'warn' | 'over' | 'primary' | 'good'; children: ReactNode }) {
  const styles = {
    neutral: 'bg-surface-2 text-ink-2',
    warn: 'bg-warn-soft text-warn',
    over: 'bg-over-soft text-over',
    primary: 'bg-primary-soft text-primary',
    good: 'bg-surface-2 text-good',
  }
  return <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${styles[tone]}`}>{children}</span>
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-ink-3">{children}</div>
}

export function Loading() {
  return <div className="p-6 text-center text-sm text-ink-3">Loading…</div>
}

export function ErrorNote({ error }: { error: unknown }) {
  return (
    <div className="rounded-lg border border-over bg-over-soft p-3 text-sm text-over">
      {error instanceof Error ? error.message : 'Something went wrong'}
    </div>
  )
}

export function PageHeader({ title, sub, action }: { title: string; sub?: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        {sub && <p className="mt-1 text-sm text-ink-2">{sub}</p>}
      </div>
      {action}
    </div>
  )
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block font-medium text-ink-2">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-ink-3">{hint}</span>}
    </label>
  )
}

export const inputBase =
  'rounded-lg border border-border bg-surface px-3 py-1.5 text-sm text-ink placeholder:text-ink-3 focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary-soft'
export const inputClass = `${inputBase} w-full`
