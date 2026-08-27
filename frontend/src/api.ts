import type { OverviewData, ProjectListResponse, ProjectDetail, AlertItem, AnalyticsData } from './types'

import overviewMock from './mocks/overview.json'
import projectsMock from './mocks/projects.json'
import projectDetailMock from './mocks/project_detail.json'
import alertsMock from './mocks/alerts.json'
import analyticsMock from './mocks/analytics.json'

async function safeFetch<T>(url: string, fallback: T): Promise<T> {
  try {
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json() as T
  } catch {
    return fallback
  }
}

export async function fetchOverview(): Promise<OverviewData> {
  return safeFetch<OverviewData>('/api/overview', overviewMock as unknown as OverviewData)
}

export async function fetchProjects(): Promise<ProjectListResponse> {
  return safeFetch<ProjectListResponse>('/api/projects', projectsMock as unknown as ProjectListResponse)
}

export async function fetchProjectDetail(id: string): Promise<ProjectDetail> {
  return safeFetch<ProjectDetail>(`/api/projects/${id}`, projectDetailMock as unknown as ProjectDetail)
}

export async function fetchAlerts(): Promise<AlertItem[]> {
  return safeFetch<AlertItem[]>('/api/alerts', alertsMock as unknown as AlertItem[])
}

export async function fetchAnalytics(): Promise<AnalyticsData> {
  return safeFetch<AnalyticsData>('/api/analytics', analyticsMock as unknown as AnalyticsData)
}

export async function postReview(id: string, action: string): Promise<{ status: string }> {
  try {
    const res = await fetch(`/api/projects/${id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return await res.json()
  } catch {
    return { status: 'recorded (offline)' }
  }
}
