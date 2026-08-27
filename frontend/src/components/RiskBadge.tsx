import { TIER_COLORS } from '../constants'

interface RiskBadgeProps {
  tier: string
}

export function RiskBadge({ tier }: RiskBadgeProps) {
  const colors = TIER_COLORS[tier] || TIER_COLORS.LOW
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold"
      style={{ backgroundColor: colors.bg, color: colors.text }}
    >
      {tier}
    </span>
  )
}
