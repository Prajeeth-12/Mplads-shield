import { TIER_COLORS } from '../constants'
import type { EvidenceItem as EvidenceItemType } from '../types'

function getTierForPoints(points: number): string {
  if (points >= 18) return 'CRITICAL'
  if (points >= 12) return 'HIGH'
  if (points >= 6) return 'MEDIUM'
  return 'LOW'
}

interface EvidenceItemProps {
  item: EvidenceItemType
}

export function EvidenceItemCard({ item }: EvidenceItemProps) {
  const tier = getTierForPoints(item.points)
  const colors = TIER_COLORS[tier]

  return (
    <div className="bg-surface rounded-lg p-4 border border-gray-100 shadow-sm">
      <div className="flex items-start gap-3">
        <span
          className="inline-flex items-center justify-center w-10 h-10 rounded-lg text-sm font-bold shrink-0"
          style={{ backgroundColor: colors.bg, color: colors.text }}
        >
          {item.points}
        </span>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-ink">{item.headline}</p>
          <p className="text-sm text-ink-2 mt-1">{item.detail}</p>
          {item.peer_context && (
            <p className="text-xs text-muted mt-2">
              Peer group: {item.peer_context.group as string || 'N/A'} (n={String(item.peer_context.n || '-')})
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
