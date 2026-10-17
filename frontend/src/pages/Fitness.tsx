import { useState } from 'react'

import { useFitness } from '../api/hooks'
import type { RangeKey } from '../api/types'
import { TrendChart } from '../components/charts'
import { Card, Empty, ErrorNote, Loading, PageHeader, RangePicker, Stat } from '../components/ui'
import { duration, pace } from '../lib/format'

const RACES = [
  { key: 'race_5k_s', label: '5K', miles: 3.10686, color: 'var(--series-1)' },
  { key: 'race_10k_s', label: '10K', miles: 6.21371, color: 'var(--series-2)' },
  { key: 'race_half_s', label: 'Half', miles: 13.1094, color: 'var(--series-3)' },
  { key: 'race_full_s', label: 'Marathon', miles: 26.2188, color: 'var(--series-4)' },
] as const

export default function Fitness() {
  const [range, setRange] = useState<RangeKey>('6m')
  const q = useFitness(range)
  const series = q.data?.series ?? []
  const latest = q.data?.latest
  // Race predictions plotted as pace so all four distances share one sensible axis.
  const racePaces = series.map((d) => ({
    day: d.day,
    ...Object.fromEntries(RACES.map((r) => [r.key, d[r.key] ? d[r.key]! / r.miles : null])),
  }))

  return (
    <>
      <PageHeader title="Fitness" sub="Garmin's fitness estimates over time." action={<RangePicker value={range} onChange={setRange} />} />
      {q.error && <ErrorNote error={q.error} />}
      {q.isLoading && <Loading />}
      {q.data && !series.length && <Empty>No fitness data yet. It arrives with your next Garmin sync.</Empty>}
      {!!series.length && latest && (
        <>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Stat label="VO2 max" value={latest.vo2max ?? '–'} />
            <Stat label="Resting HR" value={latest.resting_hr ? `${latest.resting_hr} bpm` : '–'} />
            <Stat label="Predicted 5K" value={duration(latest.race_5k_s)} sub={`Half ${duration(latest.race_half_s)}`} />
            <Stat
              label="Lactate threshold"
              value={pace(latest.lt_pace_s_per_mile)}
              sub={latest.lt_hr ? `${latest.lt_hr} bpm` : undefined}
            />
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <Card title="VO2 max">
              <TrendChart data={series} series={[{ key: 'vo2max', label: 'VO2 max', color: 'var(--series-1)', format: (v) => v.toFixed(1) }]} />
            </Card>
            <Card title="Resting heart rate">
              <TrendChart data={series} series={[{ key: 'resting_hr', label: 'Resting HR', color: 'var(--series-1)', format: (v) => `${v} bpm` }]} />
            </Card>
            <Card title="Race predictions (pace per mile)" className="lg:col-span-2">
              <TrendChart
                data={racePaces}
                reversed
                height={260}
                yFormat={(v) => duration(v)}
                series={RACES.map((r) => ({ key: r.key, label: r.label, color: r.color, format: (v: number) => `${pace(v)} · ${duration(v * r.miles)}` }))}
              />
              <p className="mt-2 text-xs text-ink-3">Faster is higher. Tooltips show pace and predicted finish time.</p>
            </Card>
            <Card title="Lactate threshold pace">
              <TrendChart data={series} reversed yFormat={(v) => duration(v)} series={[{ key: 'lt_pace_s_per_mile', label: 'LT pace', color: 'var(--series-1)', format: pace }]} />
            </Card>
            <Card title="Lactate threshold heart rate">
              <TrendChart data={series} series={[{ key: 'lt_hr', label: 'LT HR', color: 'var(--series-1)', format: (v) => `${v} bpm` }]} />
            </Card>
          </div>
        </>
      )}
    </>
  )
}
