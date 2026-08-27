import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { fetchProjectDetail, postReview } from '../api'
import { RiskBadge } from '../components/RiskBadge'
import { ScoreBar } from '../components/ScoreBar'
import { EvidenceItemCard } from '../components/EvidenceItem'
import type { ProjectDetail } from '../types'
import { DIMENSION_CAPS } from '../constants'

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<ProjectDetail | null>(null)
  const [reviewStatus, setReviewStatus] = useState<string | null>(null)

  useEffect(() => {
    if (id) fetchProjectDetail(id).then(setData)
  }, [id])

  if (!data) return <div className="text-muted">Loading...</div>

  const { project, score, evidence, financials, progress, duplicates, history, explanation } = data

  // Build timeline data combining expenditure and progress
  const timelineData = progress.map((p) => {
    const cumulativeSpent = financials
      .filter((f) => f.txn_date <= p.update_date)
      .reduce((sum, f) => sum + f.amount, 0)
    const spentPct = (cumulativeSpent / project.sanctioned_amount) * 100
    return {
      date: p.update_date,
      progress_pct: p.progress_pct,
      expenditure_pct: Math.round(spentPct * 10) / 10,
    }
  })

  const sortedEvidence = [...evidence].sort((a, b) => b.points - a.points)

  async function handleReview(action: string) {
    if (!id) return
    const res = await postReview(id, action)
    setReviewStatus(`Action "${action}" ${res.status}`)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-bold text-ink">{project.work_name}</h2>
            <p className="text-sm text-muted mt-1">
              {project.project_id} | {project.district}, {project.state} | {project.category} | {project.status}
            </p>
          </div>
          <RiskBadge tier={score.tier} />
        </div>
      </div>

      {/* Score Panel */}
      <div className="grid grid-cols-3 gap-6">
        <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100 col-span-1">
          <div className="text-center mb-4">
            <p className="text-4xl font-bold tabular-nums text-ink">{score.total}</p>
            <p className="text-sm text-muted mt-1">Risk Score</p>
            <div className="mt-2">
              <RiskBadge tier={score.tier} />
            </div>
            <p className="text-xs text-muted mt-2">Rank #{score.rank} of all projects</p>
          </div>
          <div className="mt-6">
            <ScoreBar value={score.financial} max={DIMENSION_CAPS.financial} label="Financial" tier={score.tier} />
            <ScoreBar value={score.progress} max={DIMENSION_CAPS.progress} label="Progress" tier={score.tier} />
            <ScoreBar value={score.payment} max={DIMENSION_CAPS.payment} label="Payment" tier={score.tier} />
            <ScoreBar value={score.duplication} max={DIMENSION_CAPS.duplication} label="Duplication" tier={score.tier} />
            <ScoreBar value={score.temporal} max={DIMENSION_CAPS.temporal} label="Temporal" tier={score.tier} />
            <ScoreBar value={score.compliance} max={DIMENSION_CAPS.compliance} label="Compliance" tier={score.tier} />
          </div>
        </div>

        {/* Evidence */}
        <div className="col-span-2 space-y-3">
          <h3 className="text-sm font-semibold text-ink">Evidence</h3>
          {sortedEvidence.map((e) => (
            <EvidenceItemCard key={e.code} item={e} />
          ))}
        </div>
      </div>

      {/* Timeline Chart */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Expenditure vs Progress Over Time</h3>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={(v) => `${v}%`} />
            <Line type="monotone" dataKey="expenditure_pct" stroke="#9E1E2D" name="Expenditure %" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="progress_pct" stroke="#2C6A50" name="Progress %" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Trajectory */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Risk Score Trajectory</h3>
        <ResponsiveContainer width="100%" height={120}>
          <LineChart data={history}>
            <XAxis dataKey="snapshot_date" tick={{ fontSize: 10 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Tooltip />
            <Line type="monotone" dataKey="total_score" stroke="#24408E" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Duplicates */}
      {duplicates.length > 0 && (
        <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-sm font-semibold text-ink mb-4">Potential Duplicates</h3>
          <div className="space-y-3">
            {duplicates.map((dup) => (
              <div key={dup.project_id} className="p-4 rounded-lg border border-gray-100 bg-surface-2">
                <p className="text-sm font-medium text-ink">{dup.work_name}</p>
                <p className="text-xs text-muted mt-1">
                  ID: {dup.project_id} | Similarity: {(dup.similarity * 100).toFixed(0)}% | Day gap: {dup.day_gap} | Cost ratio: {dup.cost_ratio} | Same agency: {dup.same_agency ? 'Yes' : 'No'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-2">AI Summary</h3>
        <p className="text-sm text-ink-2">{explanation.summary}</p>
        <p className="text-sm text-accent font-medium mt-3">Recommended: {explanation.action}</p>
      </div>

      {/* Action Buttons */}
      <div className="bg-surface rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-ink mb-4">Review Actions</h3>
        <div className="flex gap-3">
          <button
            onClick={() => handleReview('valid')}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-tier-low-bg text-tier-low hover:opacity-80 transition-opacity"
          >
            Mark Valid
          </button>
          <button
            onClick={() => handleReview('false_positive')}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-tier-med-bg text-tier-med hover:opacity-80 transition-opacity"
          >
            False Positive
          </button>
          <button
            onClick={() => handleReview('investigate')}
            className="px-4 py-2 rounded-lg text-sm font-medium bg-tier-crit-bg text-tier-crit hover:opacity-80 transition-opacity"
          >
            Investigate
          </button>
        </div>
        {reviewStatus && (
          <p className="text-sm text-muted mt-3">{reviewStatus}</p>
        )}
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-muted text-center py-4">
        Risk indicators are investigation signals, not findings of wrongdoing. All data shown is synthetic for demonstration purposes.
      </p>
    </div>
  )
}
