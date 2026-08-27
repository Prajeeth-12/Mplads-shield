import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchAlerts } from '../api'
import { RiskBadge } from '../components/RiskBadge'
import type { AlertItem } from '../types'

const SEVERITY_ORDER: Record<string, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 }

export function Alerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([])

  useEffect(() => {
    fetchAlerts().then(setAlerts)
  }, [])

  const sorted = [...alerts].sort(
    (a, b) => (SEVERITY_ORDER[a.severity] ?? 4) - (SEVERITY_ORDER[b.severity] ?? 4)
  )

  const grouped: Record<string, AlertItem[]> = {}
  for (const alert of sorted) {
    if (!grouped[alert.severity]) grouped[alert.severity] = []
    grouped[alert.severity].push(alert)
  }

  return (
    <div className="space-y-6">
      <h2 className="text-lg font-semibold text-ink">Alerts</h2>

      {Object.entries(grouped).map(([severity, items]) => (
        <div key={severity}>
          <h3 className="text-sm font-semibold text-ink-2 mb-3">{severity} ({items.length})</h3>
          <div className="space-y-3">
            {items.map((alert) => (
              <div
                key={alert.alert_id}
                className="bg-surface rounded-xl p-5 shadow-sm border border-gray-100"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <RiskBadge tier={alert.severity} />
                    <span className="text-sm font-medium text-ink">{alert.work_name}</span>
                  </div>
                  <span className="text-sm font-bold tabular-nums text-muted">{alert.score}</span>
                </div>
                <p className="text-sm text-ink-2 mt-2">{alert.headline}</p>
                <p className="text-xs text-muted mt-2">
                  Recommended: {alert.recommended_action}
                </p>
                <div className="mt-3 flex items-center justify-between">
                  <Link
                    to={`/project/${alert.project_id}`}
                    className="text-xs font-medium text-accent hover:underline"
                  >
                    View Project Details
                  </Link>
                  <span className="text-xs text-muted">
                    {new Date(alert.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-[10px] text-muted mt-3 border-t border-gray-100 pt-2">
                  Risk indicators are investigation signals, not findings of wrongdoing.
                </p>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
