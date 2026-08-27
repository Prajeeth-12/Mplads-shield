import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProjects } from '../api'
import { RiskBadge } from '../components/RiskBadge'
import type { ProjectListItem } from '../types'

export function Monitor() {
  const [items, setItems] = useState<ProjectListItem[]>([])
  const [filter, setFilter] = useState<string>('ALL')

  useEffect(() => {
    fetchProjects().then((res) => setItems(res.items))
  }, [])

  const filtered = filter === 'ALL' ? items : items.filter((p) => p.tier === filter)
  const sorted = [...filtered].sort((a, b) => b.score - a.score)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-ink">Project Monitor</h2>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-surface"
        >
          <option value="ALL">All Tiers</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div className="bg-surface rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-surface-2">
              <th className="text-left px-4 py-3 font-medium text-muted">ID</th>
              <th className="text-left px-4 py-3 font-medium text-muted">Work Name</th>
              <th className="text-left px-4 py-3 font-medium text-muted">District</th>
              <th className="text-left px-4 py-3 font-medium text-muted">Category</th>
              <th className="text-right px-4 py-3 font-medium text-muted">Sanctioned</th>
              <th className="text-right px-4 py-3 font-medium text-muted">Spent</th>
              <th className="text-right px-4 py-3 font-medium text-muted">Progress</th>
              <th className="text-right px-4 py-3 font-medium text-muted">Score</th>
              <th className="text-center px-4 py-3 font-medium text-muted">Tier</th>
              <th className="text-left px-4 py-3 font-medium text-muted">Top Reason</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((p) => (
              <tr
                key={p.project_id}
                className="border-b border-gray-50 hover:bg-surface-2 transition-colors"
              >
                <td className="px-4 py-3">
                  <Link to={`/project/${p.project_id}`} className="text-accent font-medium hover:underline">
                    {p.project_id}
                  </Link>
                </td>
                <td className="px-4 py-3 text-ink max-w-[200px] truncate">{p.work_name}</td>
                <td className="px-4 py-3 text-ink-2">{p.district}</td>
                <td className="px-4 py-3 text-ink-2">{p.category}</td>
                <td className="px-4 py-3 text-right tabular-nums">{p.sanctioned_amount}</td>
                <td className="px-4 py-3 text-right tabular-nums">{p.total_expenditure}</td>
                <td className="px-4 py-3 text-right tabular-nums">{p.progress_pct}%</td>
                <td className="px-4 py-3 text-right tabular-nums font-semibold">{p.score}</td>
                <td className="px-4 py-3 text-center">
                  <RiskBadge tier={p.tier} />
                </td>
                <td className="px-4 py-3 text-muted text-xs max-w-[200px] truncate">{p.top_reason || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
