import React, { useState } from 'react'
import { Bot, Github, AlertCircle } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [githubLoading, setGithubLoading] = useState(false)
  
  const { login, loginWithGitHub } = useAuth()
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string } } } }
      setError(errorObj.response?.data?.error?.message || 'Invalid email or password.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleGitHubClick = async () => {
    setError(null)
    setGithubLoading(true)
    try {
      await loginWithGitHub()
    } catch (err: unknown) {
      const errorObj = err as { response?: { data?: { error?: { message?: string }; detail?: string } } }
      if (!errorObj.response) {
        setError('Cannot connect to backend API server. Please ensure the backend is running at http://localhost:8000.')
      } else {
        const msg =
          errorObj.response.data?.error?.message ||
          errorObj.response.data?.detail ||
          'GitHub OAuth is not configured on this server. Please set GITHUB_CLIENT_ID in your backend .env file or sign in with Email & Password.'
        setError(msg)
      }
    } finally {
      setGithubLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0b0f17] flex items-center justify-center p-4">
      <div className="w-full max-w-md glass-card p-8 rounded-2xl border border-slate-800 space-y-6 shadow-2xl">
        <div className="text-center space-y-2">
          <div className="inline-flex p-3 bg-gradient-to-tr from-brand-600 to-indigo-500 rounded-xl text-white shadow-lg shadow-brand-500/20">
            <Bot className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Welcome to ReviewAI</h1>
          <p className="text-sm text-slate-400">Sign in to manage automated code review workflows</p>
        </div>

        {error && (
          <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-lg flex items-start space-x-2 text-rose-400 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span className="leading-tight">{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="developer@company.com"
              required
              className="w-full px-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full px-4 py-2.5 bg-slate-900/60 border border-slate-800 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-medium rounded-lg shadow-lg shadow-brand-600/30 transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
          >
            {submitting ? (
              <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>

        <div className="relative flex py-2 items-center">
          <div className="flex-grow border-t border-slate-800"></div>
          <span className="flex-shrink mx-4 text-xs text-slate-500 uppercase">Or continue with</span>
          <div className="flex-grow border-t border-slate-800"></div>
        </div>

        <button
          onClick={handleGitHubClick}
          disabled={githubLoading}
          className="w-full py-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-medium rounded-lg flex items-center justify-center space-x-2 transition-colors disabled:opacity-50"
        >
          {githubLoading ? (
            <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          ) : (
            <>
              <Github className="w-5 h-5" />
              <span>GitHub Account</span>
            </>
          )}
        </button>

        <div className="pt-2 text-center">
          <button
            type="button"
            onClick={() => {
              setEmail('abdulrahmanrifayath264@gmail.com')
              setPassword('password123')
            }}
            className="text-xs text-brand-400 hover:text-brand-300 underline underline-offset-4 transition-colors"
          >
            Auto-fill Local Developer Credentials
          </button>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
