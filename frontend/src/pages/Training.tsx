import { useState } from 'react'

import { useTraining } from '../api/hooks'
import type { RangeKey } from '../api/types'
import { DailyLoadChart, TrendChart } from '../components/charts'
import { Badge, Card, Empty, ErrorNote, Loading, PageHeader, RangePicker, Segmented, Stat } from '../components/ui'
import { loadPref, savePref, shortDate, titleCase } from '../lib/format'

type LoadView = 'combined' | 'split'
const LOAD_VIEW_PREF = 'unicorn.loadView'

function acwrNote(acwr: number | null | undefined) {
  if (acwr === null || acwr === undefined) return { text: 'No data', tone: undefined }
  if (acwr > 1.5) return { text: 'High injury risk: load is ramping fast', tone: 'over' as const }
  if (acwr > 1.3) return { text: 'Above the safe range', tone: 'warn' as const }
  if (acwr < 0.8) return { text: 'Below range: losing fitness', tone: 'warn' as const }
  return { text: 'In the safe range (0.8–1.3)', tone: 'good' as const }
}

export default function Training() {
  const [range, setRange] = useState<RangeKey>('3m')
  const [view, setView] = useState<LoadView>(() => loadPref(LOAD_VIEW_PREF, 'combined', ['combined', 'split'] as const))
  const q = useTraining(range)
  const series = q.data?.series ?? []
  const latest = q.data?.latest
  const note = acwrNote(latest?.acwr)
  const dailyLoad = q.data?.daily_load ?? []
  const changeView = (v: LoadView) => {
    setView(v)
    savePref(LOAD_VIEW_PREF, v)
  }

  // Collapse the daily status into runs of the same status for a compact timeline.
  const timeline: { status: string; from: string; to: string }[] = []
  for (const d of series) {
    if (!d.training_status) continue
    const last = timeline[timeline.length - 1]
    if (last && last.status === d.training_status) last.to = d.day
    else timeline.push({ status: d.training_status, from: d.day, to: d.day })
  }

  return (
    <>
      <PageHeader
        title="Training load & readiness"
        sub="Acute load is your last 7 days; chronic load is your last ~4 weeks."
        action={<RangePicker value={range} onChange={setRange} />}
      />
      {q.error && <ErrorNote error={q.error} />}
      {q.isLoading && <Loading />}
      {q.data && !series.length && <Empty>No training data yet. It arrives with your next Garmin sync.</Empty>}
      {!!series.length && latest && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="Acute : chronic" value={latest.acwr?.toFixed(2) ?? '–'} sub={note.text} tone={note.tone} />
            <Stat label="Training status" value={<span className="text-lg">{titleCase(latest.training_status)}</span>} />
            <Stat label="Readiness" value={latest.readiness_score ?? '–'} sub={titleCase(latest.readiness_level)} />
            <Stat label="HRV weekly avg" value={latest.hrv_weekly_avg ? `${latest.hrv_weekly_avg} ms` : '–'} sub={titleCase(latest.hrv_status)} />
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card
              title="Training load"
              className="lg:col-span-2"
              action={
                <Segmented
                  label="Training load view"
                  value={view}
                  onChange={changeView}
                  options={[{ key: 'combined', label: 'Combined' }, { key: 'split', label: 'Run / ride' }]}
                />
              }
            >
              {view === 'combined' && (
                <div className="mb-5">
                  <h3 className="mb-2 text-sm font-medium text-ink-2">Acute vs. chronic</h3>
                  <TrendChart
                    data={series}
                    height={260}
                    series={[
                      { key: 'acute_load', label: 'Acute (7-day)', color: 'var(--series-1)', format: (v) => String(Math.round(v)) },
                      { key: 'chronic_load', label: 'Chronic (28-day)', color: 'var(--series-2)', dashed: true, format: (v) => String(Math.round(v)) },
                    ]}
                  />
                </div>
              )}
              <h3 className="mb-2 text-sm font-medium text-ink-2">
                {view === 'combined' ? 'Daily load, all activities' : 'Daily load by sport'}
              </h3>
              <DailyLoadChart data={dailyLoad} split={view === 'split'} />
            </Card>
            <Card title="Acute : chronic workload ratio">
              <TrendChart
                data={series}
                band={{ y1: 0.8, y2: 1.3, label: 'Safe range' }}
                yDomain={[0.5, 'auto']}
                series={[{ key: 'acwr', label: 'ACWR', color: 'var(--series-1)', format: (v) => v.toFixed(2) }]}
              />
              <p className="mt-2 text-xs text-ink-3">Shaded band is the 0.8–1.3 range where injury risk is lowest.</p>
            </Card>
            <Card title="Training readiness">
              <TrendChart data={series} yDomain={[0, 100]} series={[{ key: 'readiness_score', label: 'Readiness', color: 'var(--series-1)' }]} />
            </Card>
            <Card title="HRV">
              <TrendChart
                data={series}
                series={[
                  { key: 'hrv_last_night', label: 'Last night', color: 'var(--series-1)', format: (v) => `${v} ms` },
                  { key: 'hrv_weekly_avg', label: 'Weekly avg', color: 'var(--series-2)', dashed: true, format: (v) => `${v} ms` },
                ]}
              />
            </Card>
            <Card title="Training status">
              <ol className="max-h-64 space-y-1.5 overflow-y-auto text-sm">
                {[...timeline].reverse().map((t) => (
                  <li key={t.from} className="flex items-center justify-between gap-2">
                    <Badge tone={/PRODUCTIVE|PEAKING/.test(t.status) ? 'primary' : /OVERREACHING|UNPRODUCTIVE|STRAINED/.test(t.status) ? 'warn' : 'neutral'}>
                      {titleCase(t.status)}
                    </Badge>
                    <span className="tabular text-ink-3">
                      {shortDate(t.from)}
                      {t.to !== t.from && ` – ${shortDate(t.to)}`}
                    </span>
                  </li>
                ))}
              </ol>
            </Card>
          </div>
        </>
      )}
    </>
  )
}
