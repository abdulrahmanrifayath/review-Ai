import { describe, it, expect, beforeEach } from 'vitest'

// Mock localStorage for Node test runner environment
const localStorageStore: Record<string, string> = {}
const mockLocalStorage = {
  getItem: (key: string) => localStorageStore[key] || null,
  setItem: (key: string, value: string) => {
    localStorageStore[key] = value
  },
  removeItem: (key: string) => {
    delete localStorageStore[key]
  },
  clear: () => {
    for (const k in localStorageStore) delete localStorageStore[k]
  },
}

if (typeof globalThis.localStorage === 'undefined') {
  ;(globalThis as any).localStorage = mockLocalStorage
}

describe('Frontend Auth State & Dashboard Utilities', () => {
  beforeEach(() => {
    localStorage.clear()
  })


  it('stores and retrieves access token correctly', () => {
    const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token'
    localStorage.setItem('access_token', mockToken)
    expect(localStorage.getItem('access_token')).toBe(mockToken)
  })

  it('formats finding severity badges accurately', () => {
    const getImpactBadge = (impact: string) => {
      switch (impact.toUpperCase()) {
        case 'HIGH':
        case 'CRITICAL':
          return 'bg-rose-500/20 border-rose-500/40 text-rose-300'
        case 'MEDIUM':
          return 'bg-amber-500/20 border-amber-500/40 text-amber-300'
        default:
          return 'bg-blue-500/20 border-blue-500/40 text-blue-300'
      }
    }

    expect(getImpactBadge('HIGH')).toContain('rose')
    expect(getImpactBadge('MEDIUM')).toContain('amber')
    expect(getImpactBadge('LOW')).toContain('blue')
  })

  it('calculates repository quality grade correctly', () => {
    const getGrade = (score: number) => {
      if (score >= 90) return 'A+'
      if (score >= 80) return 'A'
      if (score >= 70) return 'B'
      if (score >= 60) return 'C'
      return 'F'
    }

    expect(getGrade(95)).toBe('A+')
    expect(getGrade(82)).toBe('A')
    expect(getGrade(75)).toBe('B')
    expect(getGrade(40)).toBe('F')
  })

  it('filters finding list by category and severity', () => {
    const findings = [
      { id: '1', severity: 'HIGH', category: 'SECURITY', file: 'auth.py' },
      { id: '2', severity: 'MEDIUM', category: 'PERFORMANCE', file: 'db.py' },
      { id: '3', severity: 'LOW', category: 'MAINTAINABILITY', file: 'utils.py' },
    ]

    const securityOnly = findings.filter((f) => f.category === 'SECURITY')
    expect(securityOnly).toHaveLength(1)
    expect(securityOnly[0].file).toBe('auth.py')

    const highSeverityOnly = findings.filter((f) => f.severity === 'HIGH')
    expect(highSeverityOnly).toHaveLength(1)
  })
})
