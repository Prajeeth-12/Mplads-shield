export const TIER_COLORS: Record<string, { bg: string; text: string }> = {
  LOW: { bg: 'var(--color-tier-low-bg)', text: 'var(--color-tier-low)' },
  MEDIUM: { bg: 'var(--color-tier-med-bg)', text: 'var(--color-tier-med)' },
  HIGH: { bg: 'var(--color-tier-high-bg)', text: 'var(--color-tier-high)' },
  CRITICAL: { bg: 'var(--color-tier-crit-bg)', text: 'var(--color-tier-crit)' },
}

export const DIMENSION_CAPS: Record<string, number> = {
  financial: 25,
  progress: 20,
  payment: 18,
  duplication: 15,
  temporal: 12,
  compliance: 10,
}
