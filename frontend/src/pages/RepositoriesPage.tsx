import React, { useState, useEffect } from 'react'
import {
  FolderGit2,
  RefreshCw,
  GitBranch,
  GitPullRequest,
  Search,
  Lock,
  Globe,
  X,
  ChevronRight,
  BarChart3,
  Sliders,
} from 'lucide-react'
import { apiClient } from '../services/api'
import { Repository, Branch, PullRequest, Commit } from '../types'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { useAuth } from '../hooks/useAuth'

import { RepositorySettingsModal } from '../components/settings/RepositorySettingsModal'
import { QualityScoreCard } from '../components/dashboard/QualityScoreCard'

import { CommitActivityChart } from '../components/dashboard/CommitActivityChart'
import { LanguageBreakdown } from '../components/dashboard/LanguageBreakdown'
import { ReviewHistoryTimeline } from '../components/dashboard/ReviewHistoryTimeline'
import { ContributorList } from '../components/dashboard/ContributorList'
import { PerformanceDashboardCard, PerformanceFinding } from '../components/dashboard/PerformanceDashboardCard'
import { CodeQualityEngineCard, QualityMetrics, TrendPoint } from '../components/dashboard/CodeQualityEngineCard'
import { TestGeneratorCard } from '../components/dashboard/TestGeneratorCard'
import { DocGeneratorCard } from '../components/dashboard/DocGeneratorCard'
import { performanceApi, qualityApi } from '../services/api'
import { Zap, Activity, TestTube2, FileText } from 'lucide-react'

interface RepoAnalytics {
  repository_id: string
  full_name: string
  stargazers_count: number
  forks_count: number
  open_issues_count: number
  health: {
    health_score: number
    quality_score: number
    grade: string
    security_issues_count: number
    performance_issues_count: number
    code_smells_count: number
  }
  languages: Array<{ language: string; percentage: number; color: string }>
  commit_activity: Array<{ date: string; count: number }>
  contributors: Array<{ author_name: string; commits_count: number; prs_count: number }>
  review_history: Array<{
    id: string
    pr_number: number
    pr_title: string
    status: string
    quality_score: number
    findings_count: number
    created_at: string
  }>
}

export const RepositoriesPage: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [loading, setLoading] = useState(true)
  const [syncingAll, setSyncingAll] = useState(false)
  const [syncingRepoId, setSyncingRepoId] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const { loginWithGitHub } = useAuth()

  // Repository Settings Modal state
  const [settingsModalRepo, setSettingsModalRepo] = useState<Repository | null>(null)

  // Inspector state

  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null)
  const [activeTab, setActiveTab] = useState<'analytics' | 'quality' | 'performance' | 'pulls' | 'branches' | 'tests' | 'docs'>('analytics')
  const [branches, setBranches] = useState<Branch[]>([])
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([])
  const [_inspectingPR, setInspectingPR] = useState<PullRequest | null>(null)
  const [_prCommits, setPrCommits] = useState<Commit[]>([])
  const [analytics, setAnalytics] = useState<RepoAnalytics | null>(null)

  // Code Quality & Performance state
  const [qualityData, setQualityData] = useState<{
    score: number
    grade: string
    metrics: QualityMetrics
    trends: TrendPoint[]
  } | null>(null)
  const [performanceData, setPerformanceData] = useState<{
    findings: PerformanceFinding[]
    highCount: number
    mediumCount: number
    lowCount: number
  } | null>(null)

  const [modalLoading, setModalLoading] = useState(false)

  const fetchRepositories = async () => {
    try {
      const res = await apiClient.get('/github/repos')
      setRepositories(res.data)
    } catch {
      setRepositories([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRepositories()
  }, [])

  const handleSyncAllRepos = async () => {
    setSyncingAll(true)
    try {
      await apiClient.post('/github/repos/sync')
      await fetchRepositories()
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } }
      alert(errorObj.response?.data?.error?.message || 'Failed to sync repositories.')
    } finally {
      setSyncingAll(false)
    }
  }

  const handleSyncSingleRepo = async (repoId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setSyncingRepoId(repoId)
    try {
      await apiClient.post(`/github/repos/${repoId}/sync`)
      await fetchRepositories()
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } }
      alert(errorObj.response?.data?.error?.message || 'Failed to sync repo details.')
    } finally {
      setSyncingRepoId(null)
    }
  }

  const openRepoInspector = async (repo: Repository, tab: 'analytics' | 'quality' | 'performance' | 'tests' | 'docs' | 'pulls' | 'branches' = 'analytics') => {
    setSelectedRepo(repo)
    setActiveTab(tab)
    setInspectingPR(null)
    setModalLoading(true)

    try {
      const [owner, name] = repo.full_name.split('/')

      if (tab === 'analytics') {
        const res = await apiClient.get(`/repositories/${repo.id}/analytics`)
        setAnalytics(res.data)
      } else if (tab === 'quality') {
        const res = await qualityApi.getRepositoryQualityScore(owner, name)
        setQualityData({
          score: res.current_quality_score,
          grade: res.grade,
          metrics: res.metrics,
          trends: res.latest_trends,
        })
      } else if (tab === 'performance') {
        const res = await performanceApi.getPullRequestFindings(owner, name, 1).catch(() => null)
        if (res) {
          setPerformanceData({
            findings: res.findings,
            highCount: res.high_impact_count,
            mediumCount: res.medium_impact_count,
            lowCount: res.low_impact_count,
          })
        } else {
          setPerformanceData({
            findings: [],
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
          })
        }
      } else if (tab === 'tests' || tab === 'docs') {
        // Interactive generation tab
      } else if (tab === 'branches') {
        const res = await apiClient.get(`/github/repos/${owner}/${name}/branches`)
        setBranches(res.data)
      } else {
        const res = await apiClient.get(`/github/repos/${owner}/${name}/pulls`)
        setPullRequests(res.data)
      }
    } catch {
      setAnalytics(null)
    } finally {
      setModalLoading(false)
    }
  }

  const switchTab = async (tab: 'analytics' | 'quality' | 'performance' | 'tests' | 'docs' | 'pulls' | 'branches') => {
    if (!selectedRepo) return
    setActiveTab(tab)
    setInspectingPR(null)
    setModalLoading(true)
    const [owner, name] = selectedRepo.full_name.split('/')
    try {
      if (tab === 'analytics') {
        const res = await apiClient.get(`/repositories/${selectedRepo.id}/analytics`)
        setAnalytics(res.data)
      } else if (tab === 'quality') {
        const res = await qualityApi.getRepositoryQualityScore(owner, name)
        setQualityData({
          score: res.current_quality_score,
          grade: res.grade,
          metrics: res.metrics,
          trends: res.latest_trends,
        })
      } else if (tab === 'performance') {
        const res = await performanceApi.getPullRequestFindings(owner, name, 1).catch(() => null)
        if (res) {
          setPerformanceData({
            findings: res.findings,
            highCount: res.high_impact_count,
            mediumCount: res.medium_impact_count,
            lowCount: res.low_impact_count,
          })
        } else {
          setPerformanceData({
            findings: [],
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
          })
        }
      } else if (tab === 'tests' || tab === 'docs') {
        // Interactive generator tabs
      } else if (tab === 'branches') {
        const res = await apiClient.get(`/github/repos/${owner}/${name}/branches`)
        setBranches(res.data)
      } else {
        const res = await apiClient.get(`/github/repos/${owner}/${name}/pulls`)
        setPullRequests(res.data)
      }
    } catch {
      // Handled
    } finally {
      setModalLoading(false)
    }
  }

  const inspectPRCommits = async (pr: PullRequest) => {
    if (!selectedRepo) return
    setInspectingPR(pr)
    setModalLoading(true)
    const [owner, name] = selectedRepo.full_name.split('/')
    try {
      const res = await apiClient.get(`/github/repos/${owner}/${name}/pulls/${pr.pr_number}/commits`)
      setPrCommits(res.data)
    } catch {
      setPrCommits([])
    } finally {
      setModalLoading(false)
    }
  }

  const filteredRepos = repositories.filter(
    (repo) =>
      repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      repo.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (repo.language && repo.language.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  const getLanguageColor = (lang?: string) => {
    switch (lang?.toLowerCase()) {
      case 'typescript':
        return 'bg-blue-500'
      case 'python':
        return 'bg-amber-500'
      case 'javascript':
        return 'bg-yellow-400'
      case 'go':
        return 'bg-cyan-400'
      default:
        return 'bg-slate-400'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Repositories</h1>
          <p className="text-sm text-slate-400">
            Repository Dashboard with real-time health metrics, quality scores, and activity timelines.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleSyncAllRepos}
            disabled={syncingAll}
            className="flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${syncingAll ? 'animate-spin' : ''}`} />
            <span>{syncingAll ? 'Syncing...' : 'Sync GitHub Repos'}</span>
          </button>
          <button
            onClick={loginWithGitHub}
            className="flex items-center space-x-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-sm font-medium rounded-lg shadow-lg shadow-brand-600/20 transition-all"
          >
            <FolderGit2 className="w-4 h-4" />
            <span>Connect GitHub</span>
          </button>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="relative">
        <Search className="w-5 h-5 text-slate-500 absolute left-3 top-3" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Filter repositories by name or language..."
          className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
        />
      </div>

      {/* Repositories Grid */}
      {loading ? (
        <LoadingSpinner />
      ) : filteredRepos.length === 0 ? (
        <div className="glass-card p-12 rounded-xl border border-slate-800 text-center space-y-4">
          <FolderGit2 className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-lg font-semibold text-slate-300">No Repositories Found</h3>
          <p className="text-sm text-slate-500 max-w-md mx-auto">
            Click "Sync GitHub Repos" to synchronize accessible repositories from your connected account.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredRepos.map((repo) => (
            <div
              key={repo.id}
              onClick={() => openRepoInspector(repo, 'analytics')}
              className="glass-card p-5 rounded-xl border border-slate-800 hover:border-brand-500/40 transition-all cursor-pointer group flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {repo.is_private ? (
                      <Lock className="w-4 h-4 text-amber-400" />
                    ) : (
                      <Globe className="w-4 h-4 text-emerald-400" />
                    )}
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      {repo.owner_login}
                    </span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSettingsModalRepo(repo)
                    }}
                    className="p-1.5 text-slate-500 hover:text-brand-400 hover:bg-slate-800 rounded-lg transition-colors"
                    title="Repository Settings"
                  >
                    <Sliders className="w-3.5 h-3.5 text-slate-400 hover:text-brand-400" />
                  </button>
                  <button
                    onClick={(e) => handleSyncSingleRepo(repo.id, e)}
                    disabled={syncingRepoId === repo.id}
                    className="p-1.5 text-slate-500 hover:text-brand-400 hover:bg-slate-800 rounded-lg transition-colors"
                  >
                    <RefreshCw
                      className={`w-3.5 h-3.5 ${syncingRepoId === repo.id ? 'animate-spin text-brand-400' : ''}`}
                    />
                  </button>
                </div>

                <h3 className="text-base font-bold text-slate-100 group-hover:text-brand-400 transition-colors mt-2 truncate">
                  {repo.name}
                </h3>
              </div>

              <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                <div className="flex items-center space-x-3">
                  {repo.language && (
                    <div className="flex items-center space-x-1.5">
                      <span className={`w-2 h-2 rounded-full ${getLanguageColor(repo.language)}`}></span>
                      <span>{repo.language}</span>
                    </div>
                  )}
                  <div className="flex items-center space-x-1">
                    <GitBranch className="w-3.5 h-3.5 text-slate-500" />
                    <span>{repo.default_branch}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      setSettingsModalRepo(repo)
                    }}
                    className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium text-xs flex items-center space-x-1"
                  >
                    <Sliders className="w-3.5 h-3.5 text-brand-400" />
                    <span>Settings</span>
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      openRepoInspector(repo, 'analytics')
                    }}
                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded font-medium text-xs flex items-center space-x-1"
                  >
                    <BarChart3 className="w-3.5 h-3.5 text-brand-400" />
                    <span>Dashboard</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Repository Settings Modal */}
      {settingsModalRepo && (
        <RepositorySettingsModal
          repositoryId={settingsModalRepo.id}
          repositoryName={settingsModalRepo.full_name}
          isOpen={!!settingsModalRepo}
          onClose={() => setSettingsModalRepo(null)}
        />
      )}

      {/* Inspector Modal */}
      {selectedRepo && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-5xl glass-card bg-[#0f1522] border border-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div>
                <div className="flex items-center space-x-2">
                  <FolderGit2 className="w-5 h-5 text-brand-400" />
                  <h2 className="text-xl font-bold text-slate-100">{selectedRepo.full_name}</h2>
                </div>
                <p className="text-xs text-slate-400 mt-1">Default Branch: {selectedRepo.default_branch}</p>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setSettingsModalRepo(selectedRepo)}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold flex items-center space-x-1.5"
                >
                  <Sliders className="w-4 h-4 text-brand-400" />
                  <span>Settings</span>
                </button>
                <button
                  onClick={() => setSelectedRepo(null)}
                  className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>


            {/* Modal Tabs */}
            <div className="px-6 border-b border-slate-800 flex items-center space-x-4 overflow-x-auto">
              <button
                onClick={() => switchTab('analytics')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'analytics'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                <span>Health & Analytics</span>
              </button>
              <button
                onClick={() => switchTab('quality')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'quality'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Activity className="w-4 h-4 text-blue-400" />
                <span>Code Quality Engine</span>
              </button>
              <button
                onClick={() => switchTab('performance')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'performance'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Zap className="w-4 h-4 text-amber-400" />
                <span>Performance Analyzer</span>
              </button>
              <button
                onClick={() => switchTab('tests')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'tests'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <TestTube2 className="w-4 h-4 text-violet-400" />
                <span>AI Test Generator</span>
              </button>
              <button
                onClick={() => switchTab('docs')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'docs'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <FileText className="w-4 h-4 text-cyan-400" />
                <span>AI Doc Generator</span>
              </button>
              <button
                onClick={() => switchTab('pulls')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'pulls'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <GitPullRequest className="w-4 h-4" />
                <span>Pull Requests</span>
              </button>
              <button
                onClick={() => switchTab('branches')}
                className={`py-3 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === 'branches'
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <GitBranch className="w-4 h-4" />
                <span>Branches</span>
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 flex-1 overflow-y-auto space-y-6">
              {modalLoading ? (
                <LoadingSpinner />
              ) : activeTab === 'analytics' && analytics ? (
                <div className="space-y-6">
                  {/* Top Stats Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <QualityScoreCard
                      score={analytics.health.quality_score}
                      healthScore={analytics.health.health_score}
                      grade={analytics.health.grade}
                      securityCount={analytics.health.security_issues_count}
                      performanceCount={analytics.health.performance_issues_count}
                      codeSmellsCount={analytics.health.code_smells_count}
                    />
                    <CommitActivityChart data={analytics.commit_activity} />
                    <LanguageBreakdown languages={analytics.languages} />
                  </div>

                  {/* Bottom Row */}
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    <ReviewHistoryTimeline reviews={analytics.review_history} />
                    <ContributorList contributors={analytics.contributors} />
                  </div>
                </div>
              ) : activeTab === 'quality' && qualityData ? (
                <CodeQualityEngineCard
                  repositoryFullName={selectedRepo.full_name}
                  currentQualityScore={qualityData.score}
                  grade={qualityData.grade}
                  metrics={qualityData.metrics}
                  trends={qualityData.trends}
                />
              ) : activeTab === 'performance' && performanceData ? (
                <PerformanceDashboardCard
                  repositoryFullName={selectedRepo.full_name}
                  prNumber={1}
                  findings={performanceData.findings}
                  highImpactCount={performanceData.highCount}
                  mediumImpactCount={performanceData.mediumCount}
                  lowImpactCount={performanceData.lowCount}
                />
              ) : activeTab === 'tests' ? (
                <TestGeneratorCard
                  repositoryFullName={selectedRepo.full_name}
                  defaultTargetFile={selectedRepo.language === 'Java' ? 'UserService.java' : selectedRepo.language === 'TypeScript' ? 'userService.ts' : 'user_service.py'}
                />
              ) : activeTab === 'docs' ? (
                <DocGeneratorCard
                  repositoryFullName={selectedRepo.full_name}
                  defaultTargetFile={selectedRepo.language === 'Java' ? 'UserService.java' : selectedRepo.language === 'TypeScript' ? 'userService.ts' : 'user_service.py'}
                />
              ) : activeTab === 'branches' ? (
                <div className="space-y-2">
                  {branches.map((b) => (
                    <div
                      key={b.name}
                      className="p-3 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between text-sm"
                    >
                      <div className="flex items-center space-x-3">
                        <GitBranch className="w-4 h-4 text-brand-400" />
                        <span className="font-semibold text-slate-200">{b.name}</span>
                      </div>
                      <span className="font-mono text-xs text-slate-500">{b.commit_sha.substring(0, 7)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                /* Pull Requests Tab */
                <div className="space-y-4">
                  {pullRequests.map((pr) => (
                    <div
                      key={pr.id}
                      className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl flex items-center justify-between"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-bold text-slate-200 text-sm">
                            #{pr.pr_number} {pr.title}
                          </span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                              pr.state === 'open'
                                ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                                : 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400'
                            }`}
                          >
                            {pr.state}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-xs text-slate-400">
                          <span>by {pr.author_login}</span>
                          <span>
                            {pr.head_branch} → {pr.base_branch}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={() => inspectPRCommits(pr)}
                        className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center space-x-1"
                      >
                        <span>Commits</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
