import { useState } from 'react'
import { Link } from 'react-router-dom'

import { useDashboard, useRuns, useWeekly } from '../api/hooks'
import type { RangeKey, Week } from '../api/types'
import { WeeklyMileageChart } from '../components/charts'
import { RunList } from '../components/RunList'
import { Badge, Card, ErrorNote, Loading, PageHeader, RangePicker, Stat } from '../components/ui'
import { mi, shortDate, titleCase } from '../lib/format'

export default function Dashboard() {
  const [range, setRange] = useState<RangeKey>('3m')
  const [selected, setSelected] = useState<Week | null>(null)
  const weekly = useWeekly(range)
  const dash = useDashboard()
  const weekRuns = useRuns({ ids: selected?.run_ids, limit: 50 }, !!selected?.run_ids.length)
  const recent = useRuns({ limit: 5 })

  const d = dash.data
  const diff = d ? d.this_week.miles - d.last_week.miles : 0
  const weeks = weekly.data?.weeks ?? []
  const avg = weeks.length ? weeks.reduce((s, w) => s + w.miles, 0) / weeks.length : 0

  return (
    <>
      <PageHeader title="Dashboard" sub="Weeks run Monday through Sunday." />
      {dash.error && <ErrorNote error={dash.error} />}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat
          label="This week"
          value={`${mi(d?.this_week.miles)} mi`}
          sub={d ? `${d.this_week.runs} runs · ${diff >= 0 ? '+' : ''}${mi(diff)} vs last week` : '…'}
        />
        <Stat label="Last week" value={`${mi(d?.last_week.miles)} mi`} sub={d ? `${d.last_week.runs} runs` : '…'} />
        <Stat
          label="Training readiness"
          value={d?.today?.readiness_score ?? '–'}
          sub={d?.today?.readiness_level ? titleCase(d.today.readiness_level) : 'From Garmin'}
          tone={(d?.today?.readiness_score ?? 100) < 40 ? 'warn' : undefined}
        />
        <Stat
          label="HRV (last night)"
          value={d?.today?.hrv_last_night ? `${d.today.hrv_last_night} ms` : '–'}
          sub={d?.today?.hrv_status ? titleCase(d.today.hrv_status) : 'From Garmin'}
          tone={d?.today?.hrv_status && d.today.hrv_status !== 'BALANCED' ? 'warn' : undefined}
        />
      </div>

      {!!d?.shoe_alerts.length && (
        <div className="mt-3 flex flex-wrap items-center gap-2 rounded-xl border border-border bg-warn-soft px-4 py-3 text-sm">
          <span aria-hidden>⚠</span>
          <span className="font-medium text-ink">Shoes nearing retirement:</span>
          {d.shoe_alerts.map((s) => (
            <Link key={s.id} to="/shoes">
              <Badge tone={s.wear === 'over' ? 'over' : 'warn'}>
                {s.name} · {Math.round(s.miles)}/{Math.round(s.retire_at_miles)} mi
              </Badge>
            </Link>
          ))}
        </div>
      )}

      <Card
        className="mt-4"
        title="Weekly mileage"
        action={<RangePicker value={range} onChange={(r) => { setRange(r); setSelected(null) }} />}
      >
        {weekly.isLoading ? (
          <Loading />
        ) : (
          <>
            <WeeklyMileageChart
              weeks={weeks}
              selected={selected?.week_start}
              onSelect={(w) => setSelected((cur) => (cur?.week_start === w.week_start ? null : w))}
            />
            <p className="mt-2 text-xs text-ink-3">
              Average {mi(avg)} mi/week over {weeks.length} weeks. Click a bar to see that week's runs.
            </p>
          </>
        )}
      </Card>

      <Card
        className="mt-4"
        title={selected ? `Week of ${shortDate(selected.week_start)} · ${mi(selected.miles)} mi` : 'Recent runs'}
        action={
          selected ? (
            <button type="button" className="text-sm text-link" onClick={() => setSelected(null)}>
              Show recent
            </button>
          ) : (
            <Link to="/runs" className="text-sm text-link">All runs →</Link>
          )
        }
      >
        {selected ? (
          selected.run_ids.length ? <RunList runs={weekRuns.data?.items ?? []} /> : <p className="text-sm text-ink-3">No runs that week.</p>
        ) : (
          <RunList runs={recent.data?.items ?? []} />
        )}
      </Card>
    </>
  )
}
