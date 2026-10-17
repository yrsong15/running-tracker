import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useRuns, useShoes } from '../api/hooks'
import { RunList } from '../components/RunList'
import { Button, Card, ErrorNote, Field, inputClass, Loading, PageHeader } from '../components/ui'

const PAGE = 25

export default function Runs() {
  const [params, setParams] = useSearchParams()
  const [page, setPage] = useState(0)
  const shoes = useShoes()
  const filters = {
    start: params.get('start') ?? undefined,
    end: params.get('end') ?? undefined,
    shoe_id: params.get('shoe') ? Number(params.get('shoe')) : undefined,
  }
  const runs = useRuns({ ...filters, limit: PAGE, offset: page * PAGE })
  const total = runs.data?.total ?? 0

  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next)
    setPage(0)
  }

  return (
    <>
      <PageHeader title="Runs" sub={runs.data ? `${total} runs` : undefined} />
      <Card>
        <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <Field label="From">
            <input type="date" className={inputClass} value={filters.start ?? ''} onChange={(e) => set('start', e.target.value)} />
          </Field>
          <Field label="To">
            <input type="date" className={inputClass} value={filters.end ?? ''} onChange={(e) => set('end', e.target.value)} />
          </Field>
          <Field label="Shoe">
            <select className={inputClass} value={params.get('shoe') ?? ''} onChange={(e) => set('shoe', e.target.value)}>
              <option value="">Any shoe</option>
              {shoes.data?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                  {s.retired_at ? ' (retired)' : ''}
                </option>
              ))}
            </select>
          </Field>
        </div>
        {runs.error && <ErrorNote error={runs.error} />}
        {runs.isLoading ? <Loading /> : <RunList runs={runs.data?.items ?? []} />}
        {total > PAGE && (
          <div className="mt-4 flex items-center justify-between text-sm text-ink-2">
            <Button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              ← Newer
            </Button>
            <span className="tabular">
              {page * PAGE + 1}–{Math.min(total, (page + 1) * PAGE)} of {total}
            </span>
            <Button disabled={(page + 1) * PAGE >= total} onClick={() => setPage((p) => p + 1)}>
              Older →
            </Button>
          </div>
        )}
      </Card>
    </>
  )
}
