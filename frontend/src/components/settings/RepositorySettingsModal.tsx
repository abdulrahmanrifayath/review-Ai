import React, { useState, useEffect } from 'react'
import {
  X,
  Save,
  RotateCcw,
  Sliders,
  FileCode,
  ShieldCheck,
  Cpu,
  GitPullRequest,
  Check,
  AlertCircle,
  RefreshCw,
} from 'lucide-react'
import { repositorySettingsApi } from '../../services/api'

export interface RepositorySettingsModalProps {
  repositoryId: string
  repositoryName: string
  isOpen: boolean
  onClose: () => void
}

export interface SettingsData {
  analysis_enabled: boolean
  auto_review_enabled: boolean
  auto_publish_github_review: boolean

  excluded_files: string[]
  excluded_directories: string[]
  supported_file_extensions: string[]
  max_file_size_kb: number

  max_cyclomatic_complexity: number
  min_maintainability_score: number
  min_severity_level: string
  max_findings_limit: number

  static_analysis_enabled: boolean
  security_analysis_enabled: boolean
  performance_analysis_enabled: boolean
  ast_analysis_enabled: boolean
  ai_review_enabled: boolean
  test_generation_enabled: boolean
  documentation_analysis_enabled: boolean

  post_inline_comments: boolean
  post_summary: boolean
  auto_publish: boolean
  review_mode: string
}

export const RepositorySettingsModal: React.FC<RepositorySettingsModalProps> = ({
  repositoryId,
  repositoryName,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'general' | 'files' | 'rules' | 'analyzers' | 'github'>('general')
  const [settings, setSettings] = useState<SettingsData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [saving, setSaving] = useState<boolean>(false)
  const [resetting, setResetting] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Tag inputs for arrays
  const [newExFile, setNewExFile] = useState<string>('')
  const [newExDir, setNewExDir] = useState<string>('')

  const fetchSettings = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await repositorySettingsApi.getSettings(repositoryId)
      setSettings(data)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch repository settings.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isOpen && repositoryId) {
      fetchSettings()
    }
  }, [isOpen, repositoryId])

  if (!isOpen) return null

  const handleSave = async () => {
    if (!settings) return
    setSaving(true)
    setError(null)
    setSuccessMessage(null)
    try {
      const updated = await repositorySettingsApi.updateSettings(repositoryId, settings as any)
      setSettings(updated)
      setSuccessMessage('Repository settings saved successfully!')
      setTimeout(() => setSuccessMessage(null), 4000)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save repository settings.')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset settings to global defaults?')) return
    setResetting(true)
    setError(null)
    setSuccessMessage(null)
    try {
      const resetData = await repositorySettingsApi.resetSettings(repositoryId)
      setSettings(resetData)
      setSuccessMessage('Settings reset to global defaults!')
      setTimeout(() => setSuccessMessage(null), 4000)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to reset repository settings.')
    } finally {
      setResetting(false)
    }
  }

  const toggleField = (field: keyof SettingsData) => {
    if (!settings) return
    setSettings({ ...settings, [field]: !settings[field] })
  }

  const handleAddExcludedFile = () => {
    if (!newExFile.trim() || !settings) return
    if (!settings.excluded_files.includes(newExFile.trim())) {
      setSettings({ ...settings, excluded_files: [...settings.excluded_files, newExFile.trim()] })
    }
    setNewExFile('')
  }

  const handleRemoveExcludedFile = (item: string) => {
    if (!settings) return
    setSettings({
      ...settings,
      excluded_files: settings.excluded_files.filter((f) => f !== item),
    })
  }

  const handleAddExcludedDir = () => {
    if (!newExDir.trim() || !settings) return
    if (!settings.excluded_directories.includes(newExDir.trim())) {
      setSettings({ ...settings, excluded_directories: [...settings.excluded_directories, newExDir.trim()] })
    }
    setNewExDir('')
  }

  const handleRemoveExcludedDir = (item: string) => {
    if (!settings) return
    setSettings({
      ...settings,
      excluded_directories: settings.excluded_directories.filter((d) => d !== item),
    })
  }

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl glass-card bg-[#0f1522] border border-slate-800 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-brand-500/10 border border-brand-500/20 rounded-xl text-brand-400">
              <Sliders className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-100">Repository Settings</h2>
              <p className="text-xs text-slate-400">{repositoryName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 border-b border-slate-800 flex items-center space-x-4 overflow-x-auto">
          {[
            { id: 'general', label: 'General', icon: Sliders },
            { id: 'files', label: 'File Rules', icon: FileCode },
            { id: 'rules', label: 'Analysis Thresholds', icon: ShieldCheck },
            { id: 'analyzers', label: 'Enabled Analyzers', icon: Cpu },
            { id: 'github', label: 'GitHub Behavior', icon: GitPullRequest },
          ].map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-3.5 text-sm font-semibold border-b-2 flex items-center space-x-2 whitespace-nowrap transition-colors ${
                  activeTab === tab.id
                    ? 'border-brand-500 text-brand-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            )
          })}
        </div>

        {/* Modal Body */}
        <div className="p-6 flex-1 overflow-y-auto space-y-6">
          {error && (
            <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center space-x-3 text-rose-400 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center space-x-3 text-emerald-400 text-sm">
              <Check className="w-5 h-5 flex-shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}

          {loading ? (
            <div className="p-12 flex flex-col items-center justify-center space-y-3 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-brand-400" />
              <span className="text-sm font-medium">Loading repository configuration...</span>
            </div>
          ) : settings ? (
            <div>
              {/* Tab 1: General Settings */}
              {activeTab === 'general' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-200">General Automation & Review Flags</h3>
                    <p className="text-xs text-slate-400">Control high-level code review automation behavior.</p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <div>
                        <h4 className="text-sm font-semibold text-slate-200">Enable ReviewAI Analysis</h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          When disabled, review requests and webhooks for this repository will be skipped.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleField('analysis_enabled')}
                        className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                          settings.analysis_enabled ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                        }`}
                      >
                        <span className="w-4 h-4 bg-white rounded-full shadow-md" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <div>
                        <h4 className="text-sm font-semibold text-slate-200">Automatic PR Review Ingestion</h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Automatically run analysis pipeline whenever GitHub PR opened/synchronized events occur.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleField('auto_review_enabled')}
                        className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                          settings.auto_review_enabled ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                        }`}
                      >
                        <span className="w-4 h-4 bg-white rounded-full shadow-md" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <div>
                        <h4 className="text-sm font-semibold text-slate-200">Auto-Publish Review Payload to GitHub</h4>
                        <p className="text-xs text-slate-400 mt-0.5">
                          Automatically write back consolidated review summaries and inline comments to GitHub PRs.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleField('auto_publish_github_review')}
                        className={`w-12 h-6 flex items-center rounded-full p-1 transition-colors ${
                          settings.auto_publish_github_review ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                        }`}
                      >
                        <span className="w-4 h-4 bg-white rounded-full shadow-md" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: File Exclusions & Rules */}
              {activeTab === 'files' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-200">File Rules & Path Exclusions</h3>
                    <p className="text-xs text-slate-400">
                      Excluded files and directories are filtered out before running Tree-sitter AST and static linters.
                    </p>
                  </div>

                  {/* Excluded Directories */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-300">Excluded Directories</label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="e.g. node_modules, dist, vendor"
                        value={newExDir}
                        onChange={(e) => setNewExDir(e.target.value)}
                        className="flex-1 px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      />
                      <button
                        type="button"
                        onClick={handleAddExcludedDir}
                        className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
                      >
                        Add Dir
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {settings.excluded_directories.map((dir) => (
                        <span
                          key={dir}
                          className="px-2.5 py-1 bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-lg flex items-center space-x-1.5"
                        >
                          <span>{dir}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveExcludedDir(dir)}
                            className="text-slate-500 hover:text-rose-400"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Excluded Files */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-300">Excluded File Names / Patterns</label>
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        placeholder="e.g. package-lock.json, .min.js"
                        value={newExFile}
                        onChange={(e) => setNewExFile(e.target.value)}
                        className="flex-1 px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      />
                      <button
                        type="button"
                        onClick={handleAddExcludedFile}
                        className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold"
                      >
                        Add File
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1.5 pt-2">
                      {settings.excluded_files.map((file) => (
                        <span
                          key={file}
                          className="px-2.5 py-1 bg-slate-900 border border-slate-800 text-slate-300 text-xs rounded-lg flex items-center space-x-1.5"
                        >
                          <span>{file}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveExcludedFile(file)}
                            className="text-slate-500 hover:text-rose-400"
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Max File Size */}
                  <div className="space-y-2">
                    <label className="text-xs font-semibold text-slate-300">Maximum File Size Limit (KB)</label>
                    <input
                      type="number"
                      value={settings.max_file_size_kb}
                      onChange={(e) => setSettings({ ...settings, max_file_size_kb: parseInt(e.target.value) || 1024 })}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                    />
                  </div>
                </div>
              )}

              {/* Tab 3: Analysis Rules & Thresholds */}
              {activeTab === 'rules' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-200">Analysis Rules & Metrics Thresholds</h3>
                    <p className="text-xs text-slate-400">Configure complexity triggers, maintainability baselines, and severity limits.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <label className="text-xs font-semibold text-slate-200">Max Cyclomatic Complexity Threshold</label>
                      <input
                        type="number"
                        value={settings.max_cyclomatic_complexity}
                        onChange={(e) =>
                          setSettings({ ...settings, max_cyclomatic_complexity: parseInt(e.target.value) || 15 })
                        }
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      />
                      <p className="text-[11px] text-slate-400">Functions exceeding this threshold will trigger complexity code smells.</p>
                    </div>

                    <div className="space-y-2 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <label className="text-xs font-semibold text-slate-200">Min Maintainability Score Baseline</label>
                      <input
                        type="number"
                        value={settings.min_maintainability_score}
                        onChange={(e) =>
                          setSettings({ ...settings, min_maintainability_score: parseInt(e.target.value) || 60 })
                        }
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      />
                      <p className="text-[11px] text-slate-400">Maintainability score baseline (0-100 scale).</p>
                    </div>

                    <div className="space-y-2 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <label className="text-xs font-semibold text-slate-200">Minimum Severity Level to Report</label>
                      <select
                        value={settings.min_severity_level}
                        onChange={(e) => setSettings({ ...settings, min_severity_level: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      >
                        <option value="INFO">INFO (Report everything)</option>
                        <option value="LOW">LOW (Low, Medium, High, Critical)</option>
                        <option value="MEDIUM">MEDIUM (Medium, High, Critical)</option>
                        <option value="HIGH">HIGH (High & Critical only)</option>
                        <option value="CRITICAL">CRITICAL (Critical vulnerabilities only)</option>
                      </select>
                    </div>

                    <div className="space-y-2 p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <label className="text-xs font-semibold text-slate-200">Max Findings Displayed Limit</label>
                      <input
                        type="number"
                        value={settings.max_findings_limit}
                        onChange={(e) =>
                          setSettings({ ...settings, max_findings_limit: parseInt(e.target.value) || 50 })
                        }
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 4: Enabled Analyzers */}
              {activeTab === 'analyzers' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-200">Analyzer Modules Control</h3>
                    <p className="text-xs text-slate-400">Toggle individual analysis engines on or off for this repository.</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {[
                      { key: 'static_analysis_enabled', label: 'Static Analysis Engine (Linters)', desc: 'Run Pylint, ESLint, Checkstyle' },
                      { key: 'security_analysis_enabled', label: 'Security SAST Engine', desc: 'Detect secrets & vulnerabilities' },
                      { key: 'performance_analysis_enabled', label: 'Performance Analyzer', desc: 'Detect N+1 queries & memory bottlenecks' },
                      { key: 'ast_analysis_enabled', label: 'Tree-sitter AST Parser', desc: 'Parse AST syntax trees' },
                      { key: 'ai_review_enabled', label: 'AI Review Engine (LLM)', desc: 'Invoke OpenAI/Anthropic code reasoning' },
                      { key: 'test_generation_enabled', label: 'AI Unit Test Generator', desc: 'Enable pytest/Jest/JUnit generator' },
                      { key: 'documentation_analysis_enabled', label: 'AI Doc Generator', desc: 'Enable docstring generator' },
                    ].map((item) => (
                      <div
                        key={item.key}
                        className="flex items-center justify-between p-4 bg-slate-900/60 border border-slate-800 rounded-xl"
                      >
                        <div>
                          <h4 className="text-xs font-semibold text-slate-200">{item.label}</h4>
                          <p className="text-[11px] text-slate-400 mt-0.5">{item.desc}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => toggleField(item.key as keyof SettingsData)}
                          className={`w-11 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                            settings[item.key as keyof SettingsData] ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                          }`}
                        >
                          <span className="w-4 h-4 bg-white rounded-full shadow-md" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Tab 5: GitHub Review Behavior */}
              {activeTab === 'github' && (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <h3 className="text-base font-bold text-slate-200">GitHub Review Publication Behavior</h3>
                    <p className="text-xs text-slate-400">Configure how reviews are published back to GitHub PRs.</p>
                  </div>

                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <div>
                        <h4 className="text-xs font-semibold text-slate-200">Post Inline Review Comments</h4>
                        <p className="text-[11px] text-slate-400 mt-0.5">Post inline findings directly on modified diff lines in PRs.</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleField('post_inline_comments')}
                        className={`w-11 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                          settings.post_inline_comments ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                        }`}
                      >
                        <span className="w-4 h-4 bg-white rounded-full shadow-md" />
                      </button>
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-900/60 border border-slate-800 rounded-xl">
                      <div>
                        <h4 className="text-xs font-semibold text-slate-200">Post Executive Review Summary</h4>
                        <p className="text-[11px] text-slate-400 mt-0.5">Post overall Markdown executive review summary payload.</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => toggleField('post_summary')}
                        className={`w-11 h-5 flex items-center rounded-full p-0.5 transition-colors ${
                          settings.post_summary ? 'bg-brand-600 justify-end' : 'bg-slate-800 justify-start'
                        }`}
                      >
                        <span className="w-4 h-4 bg-white rounded-full shadow-md" />
                      </button>
                    </div>

                    <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-xl space-y-2">
                      <label className="text-xs font-semibold text-slate-200">Default GitHub PR Review Mode</label>
                      <select
                        value={settings.review_mode}
                        onChange={(e) => setSettings({ ...settings, review_mode: e.target.value })}
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-brand-500"
                      >
                        <option value="COMMENT">COMMENT (Post feedback without blocking approval)</option>
                        <option value="REQUEST_CHANGES">REQUEST CHANGES (Block merging if high severity findings exist)</option>
                        <option value="APPROVE">APPROVE (Explicitly approve if quality score &gt;= 85%)</option>

                      </select>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Modal Footer */}
        <div className="p-6 border-t border-slate-800 flex items-center justify-between bg-slate-950/40">
          <button
            type="button"
            onClick={handleReset}
            disabled={resetting || loading}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800 text-xs font-semibold rounded-lg transition-colors disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
            <span>Reset Defaults</span>
          </button>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors"
            >
              Cancel
            </button>

            <button
              type="button"
              onClick={handleSave}
              disabled={saving || loading || !settings}
              className="flex items-center space-x-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold rounded-lg shadow-lg shadow-brand-600/20 transition-all disabled:opacity-50"
            >
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              <span>Save Configuration</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
