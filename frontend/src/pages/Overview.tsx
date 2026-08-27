import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { fetchOverview } from '../api'
import { StatTile } from '../components/StatTile'
import { RiskBadge } from '../components/RiskBadge'
import type { OverviewData } from '../types'
import { TIER_COLORS } from '../constants'

export function Overview() {
  const [data, setData] = useState<OverviewData | null>(null)

  useEffect(() => {
    fetchOverview().then(setData)
  }, [])

  if (!data) return <div className="text-muted">Loading...</div>

  const tierData = [
    { name: 'LOW', value: data.tier_counts.LOW || 0, color: TIER_COLORS.LOW.text },
    { name: 'MEDIUM', value: data.tier_counts.MEDIUM || 0, color: TIER_COLORS.MEDIUM.text },
    { name: 'HIGH', value: data.tier_counts.HIGH || 0, color: TIER_COLORS.HIGH.text },
    { name: 'CRITICAL', value: data.tier_counts.CRITICAL || 0, color: TIER_COLORS.CRITICAL.text },
  ]

  const stateData = [...data.state_risk].sort((a, b) => b.high_risk_share - a.high_risk_share)

  return (
    <div className="space-y-8">
      {/* Stat tiles */}
      <div className="grid grid-cols-4 gap-4">
        <StatTile value={data.total_projects.toLocaleString()} label="Total Works" />
        <StatTile value={`${(data.total_sanctioned / 100).toFixed(1)}`} label="Total Sanctioned (Rs Cr)" />
        <StatTile value={`${(data.total_spent / 100).toFixed(1)}`} label="Total Spent (Rs Cr)" />
        <StatTile value={(data.tier_counts.HIGH || 0) + (data.tier_counts.CRITICAL || 0)} label="High Risk" />
      </div>

      {/* Tier Distribution */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Tier Distribution</h3>
        <ResponsiveContainer width="100%" height={60}>
          <BarChart data={[{ LOW: data.tier_counts.LOW, MEDIUM: data.tier_counts.MEDIUM, HIGH: data.tier_counts.HIGH, CRITICAL: data.tier_counts.CRITICAL }]} layout="vertical" barSize={24}>
            <XAxis type="number" hide />
            <YAxis type="category" dataKey="name" hide />
            <Tooltip />
            <Bar dataKey="LOW" stackId="a" fill={TIER_COLORS.LOW.text} />
            <Bar dataKey="MEDIUM" stackId="a" fill={TIER_COLORS.MEDIUM.text} />
            <Bar dataKey="HIGH" stackId="a" fill={TIER_COLORS.HIGH.text} />
            <Bar dataKey="CRITICAL" stackId="a" fill={TIER_COLORS.CRITICAL.text} />
          </BarChart>
        </ResponsiveContainer>
        <div className="flex gap-4 mt-3">
          {tierData.map((t) => (
            <div key={t.name} className="flex items-center gap-1.5 text-xs">
              <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: t.color }} />
              <span className="text-muted">{t.name}: {t.value.toLocaleString()}</span>
            </div>
          ))}
        </div>
      </div>

      {/* State Risk Ranking */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">State Risk Ranking (High-Risk Share)</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={stateData} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
            <YAxis type="category" dataKey="state" width={90} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`} />
            <Bar dataKey="high_risk_share" barSize={18} radius={[0, 4, 4, 0]}>
              {stateData.map((entry, idx) => (
                <Cell key={idx} fill={entry.high_risk_share >= 0.1 ? TIER_COLORS.CRITICAL.text : entry.high_risk_share >= 0.07 ? TIER_COLORS.HIGH.text : TIER_COLORS.MEDIUM.text} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Critical Alerts */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Latest Critical Alerts</h3>
        <div className="space-y-3">
          {data.critical_alerts.slice(0, 5).map((alert) => (
            <Link
              key={alert.alert_id}
              to={`/project/${alert.project_id}`}
              className="block p-4 rounded-lg border border-gray-100 hover:border-gray-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <RiskBadge tier={alert.severity} />
                  <span className="ml-2 text-sm font-medium text-ink">{alert.work_name}</span>
                </div>
                <span className="text-sm font-bold tabular-nums text-tier-crit">{alert.score}</span>
              </div>
              <p className="text-sm text-muted mt-1">{alert.headline}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
