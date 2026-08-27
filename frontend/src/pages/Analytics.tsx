import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { fetchAnalytics } from '../api'
import type { AnalyticsData } from '../types'

export function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null)

  useEffect(() => {
    fetchAnalytics().then(setData)
  }, [])

  if (!data) return <div className="text-muted">Loading...</div>

  const stateData = [...data.state_risk].sort((a, b) => b.high_risk_share - a.high_risk_share)

  return (
    <div className="space-y-8">
      <h2 className="text-lg font-semibold text-ink">Analytics</h2>

      {/* State Risk */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">State Risk (High-Risk Share)</h3>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={stateData} layout="vertical" margin={{ left: 100 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
            <YAxis type="category" dataKey="state" width={90} tick={{ fontSize: 12 }} />
            <Tooltip formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`} />
            <Bar dataKey="high_risk_share" fill="#24408E" barSize={16} radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Category Anomaly Rate */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Category Anomaly Rate</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.category_anomaly_rate}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="category" tick={{ fontSize: 11 }} angle={-20} textAnchor="end" height={60} />
            <YAxis tickFormatter={(v) => `${(Number(v) * 100).toFixed(0)}%`} />
            <Tooltip formatter={(v) => `${(Number(v) * 100).toFixed(1)}%`} />
            <Bar dataKey="high_risk_pct" fill="#AF4F1A" barSize={32} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Indicator Frequency */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Indicator Frequency</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.indicator_frequency}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#8A6212" barSize={40} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
