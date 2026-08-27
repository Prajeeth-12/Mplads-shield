interface StatTileProps {
  value: string | number
  label: string
}

export function StatTile({ value, label }: StatTileProps) {
  return (
    <div className="bg-surface rounded-xl p-5 shadow-sm border border-gray-100">
      <p className="text-2xl font-bold tabular-nums text-ink">{value}</p>
      <p className="text-sm text-muted mt-1">{label}</p>
    </div>
  )
}
