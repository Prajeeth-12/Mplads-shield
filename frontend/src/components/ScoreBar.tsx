import { TIER_COLORS } from '../constants'

interface ScoreBarProps {
  value: number
  max: number
  label: string
  tier: string
}

export function ScoreBar({ value, max, label, tier }: ScoreBarProps) {
  const pct = Math.min((value / max) * 100, 100)
  const colors = TIER_COLORS[tier] || TIER_COLORS.LOW

  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-ink-2 font-medium capitalize">{label}</span>
        <span className="tabular-nums font-semibold" style={{ color: colors.text }}>
          {value}/{max}
        </span>
      </div>
      <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, backgroundColor: colors.text }}
        />
      </div>
    </div>
  )
}
