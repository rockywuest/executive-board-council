import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { useDropzone } from 'react-dropzone'
import { createClient } from '@supabase/supabase-js'
import {
  Upload,
  FileText,
  Users,
  MessageSquare,
  ChevronDown,
  ChevronUp,
  Loader2,
  Building2,
  Send,
  X,
  CheckCircle2,
  AlertCircle,
  History,
  Download,
  Copy,
  AlertTriangle,
  Shield,
  Lightbulb,
  RefreshCw,
  Trash2,
  ArrowLeft,
  Factory,
  Car,
  Monitor,
  Heart,
  Landmark,
  ShoppingCart,
  Zap,
  FlaskConical,
  Truck,
  HardHat,
  LogIn,
  LogOut,
  User,
  CreditCard,
  AlertOctagon
} from 'lucide-react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

// Supabase client - uses public anon key (safe for frontend)
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
const supabase = supabaseUrl && supabaseAnonKey ? createClient(supabaseUrl, supabaseAnonKey) : null

// Translations - German is default
const TRANSLATIONS = {
  de: {
    // Header
    appTitle: 'Vorstandsgremium',
    appSubtitle: 'Entscheidungsunterstützung für deutsche Unternehmen',
    changeIndustry: 'Branche wechseln',
    history: 'Verlauf',
    export: 'Exportieren',

    // Industry Selector
    selectIndustry: 'Wählen Sie Ihre Branche',
    selectIndustryDesc: 'Wählen Sie Ihre Branche, um die Vorstandszusammensetzung und Szenarien anzupassen',
    loadingIndustries: 'Branchen werden geladen...',

    // Main Input
    presentSituation: 'Geschäftssituation präsentieren',
    templates: 'Vorlagen',
    situationPlaceholder: 'Beschreiben Sie die Geschäftssituation, Herausforderung oder Entscheidung, zu der Sie Beratung benötigen...\n\nBeispiel: Wir erwägen, unsere Produktionskapazität durch den Bau einer neuen Fabrik in Osteuropa zu erweitern. Welche Faktoren sollten wir berücksichtigen?',
    dragDropFiles: 'Dokumente hierher ziehen oder klicken zum Auswählen',
    fileTypes: 'PDF, DOC, DOCX, TXT, CSV, XLS, XLSX (max 5MB pro Datei)',
    includeDebate: 'Debattenphase einschließen',
    generateRiskMatrix: 'Risikomatrix erstellen',
    consultingBoard: 'Vorstand wird konsultiert...',
    conveneBoard: 'Vorstand einberufen',

    // Stages
    stagePerspectives: 'Perspektiven',
    stageEvaluation: 'Bewertung',
    stageDebate: 'Debatte',
    stageRiskAnalysis: 'Risikoanalyse',
    stageSynthesis: 'Synthese',

    // Results
    expandAll: 'Alle aufklappen',
    collapseAll: 'Alle zuklappen',
    copySynthesis: 'Synthese kopieren',
    stage1Title: 'Phase 1: Vorstandsperspektiven',
    stage2Title: 'Phase 2: Gegenseitige Bewertungen',
    stage2_5Title: 'Phase 2.5: Debattenantworten',
    stage3Title: 'Phase 3: Empfehlung des Ratssprechers',
    aggregateRankings: 'Gesamtranking',
    keyUncertainties: 'Zentrale Unsicherheiten',
    evaluationBy: 'Bewertung durch',
    responds: 'antwortet',
    debateResponse: 'Debattenantwort',

    // Risk Matrix
    riskMatrix: 'Risikomatrix',
    risk: 'Risiko',
    category: 'Kategorie',
    level: 'Stufe',
    owner: 'Verantwortlich',
    mitigation: 'Maßnahmen',

    // Meeting History
    meetingHistory: 'Besprechungsverlauf',
    noPreviousMeetings: 'Keine vorherigen Besprechungen',
    discussions: 'Diskussion(en)',
    deleteMeeting: 'Besprechung löschen',

    // Footer
    footerVersion: 'Vorstandsgremium v3.0 - Unterstützt durch mehrere KI-Modelle via OpenRouter',
    footerFeatures: 'Funktionen: Branchenauswahl • Advocatus Diaboli • Debattenphase • Risikomatrix • Konfidenzwerte',

    // Misc
    all: 'Alle',
    avg: 'Durchschn.',

    // Auth
    login: 'Anmelden',
    logout: 'Abmelden',
    register: 'Registrieren',
    email: 'E-Mail',
    password: 'Passwort',
    loginTitle: 'Anmelden',
    registerTitle: 'Registrieren',
    noAccount: 'Noch kein Konto?',
    hasAccount: 'Bereits ein Konto?',
    loginError: 'Anmeldung fehlgeschlagen. Bitte prüfen Sie Ihre Zugangsdaten.',
    registerError: 'Registrierung fehlgeschlagen. Bitte versuchen Sie es erneut.',
    registerSuccess: 'Registrierung erfolgreich! Bitte prüfen Sie Ihre E-Mails zur Bestätigung.',

    // Usage & Tiers
    usage: 'Nutzung',
    remaining: 'Verbleibend',
    requestsRemaining: 'Anfragen verbleibend',
    requestsToday: 'Heute',
    requestsMonth: 'Diesen Monat',
    unlimited: 'Unbegrenzt',
    upgrade: 'Upgrade',
    upgradeToPro: 'Auf Pro upgraden',
    limitReached: 'Limit erreicht',
    limitReachedTitle: 'Anfragelimit erreicht',
    limitReachedAnon: 'Sie haben Ihr tägliches Limit von 2 kostenlosen Anfragen erreicht. Erstellen Sie ein kostenloses Konto für 5 Anfragen pro Monat, oder upgraden Sie auf Pro für 50 Anfragen.',
    limitReachedFree: 'Sie haben Ihr monatliches Limit von 5 Anfragen erreicht. Upgraden Sie auf Pro für 50 Anfragen pro Monat.',
    createAccount: 'Kostenloses Konto erstellen',
    tier: 'Tarif',
    tierAnonymous: 'Anonym',
    tierFree: 'Kostenlos',
    tierPro: 'Pro',
    tierEnterprise: 'Enterprise',

    // Error messages
    failedCreateMeeting: 'Besprechung konnte nicht erstellt werden',
    failedLoadMeeting: 'Besprechung konnte nicht geladen werden',
    confirmDeleteMeeting: 'Diese Besprechung wirklich löschen?',
    failedDeleteMeeting: 'Besprechung konnte nicht gelöscht werden',
    copiedToClipboard: 'In Zwischenablage kopiert!',
    failedExportMeeting: 'Besprechung konnte nicht exportiert werden',
    failedSubmit: 'Absenden fehlgeschlagen',
    removeFile: 'Entfernen',
  },
}
const t = TRANSLATIONS.de

// Default executive info (manufacturing) - will be replaced by dynamic data
const DEFAULT_EXECUTIVE_INFO = {
  CEO: { title: 'Chief Executive Officer', german: 'Vorstandsvorsitzender', color: '#2563eb', icon: '👔' },
  CFO: { title: 'Chief Financial Officer', german: 'Finanzvorstand', color: '#059669', icon: '💰' },
  CTO: { title: 'Chief Technology Officer', german: 'Technischer Vorstand', color: '#7c3aed', icon: '⚙️' },
  CHRO: { title: 'Chief Human Resources Officer', german: 'Personalvorstand', color: '#db2777', icon: '👥' },
  CSO: { title: 'Chief Sales Officer', german: 'Vertriebsvorstand', color: '#ea580c', icon: '📈' },
  CPO_CSCO: { title: 'Chief Purchasing & Supply Chain Officer', german: 'Einkaufs- und Supply Chain Vorstand', color: '#0891b2', icon: '🔗' },
  DEVILS_ADVOCATE: { title: "Devil's Advocate", german: 'Advocatus Diaboli', color: '#dc2626', icon: '😈' },
}

// Icon mapping for industries
const INDUSTRY_ICONS = {
  manufacturing: Factory,
  automotive: Car,
  technology: Monitor,
  healthcare: Heart,
  financial: Landmark,
  retail: ShoppingCart,
  energy: Zap,
  chemicals: FlaskConical,
  logistics: Truck,
  construction: HardHat,
}

// Color assignments for executive roles
const ROLE_COLORS = {
  CEO: '#2563eb',
  CFO: '#059669',
  CTO: '#7c3aed',
  CHRO: '#db2777',
  CSO: '#ea580c',
  CPO_CSCO: '#0891b2',
  CPO: '#0891b2',
  CISO: '#6366f1',
  CMO: '#f59e0b',
  CRO: '#8b5cf6',
  CCO: '#ec4899',
  COO: '#14b8a6',
  CLO: '#64748b',
  DEVILS_ADVOCATE: '#dc2626',
}

// Icon assignments for executive roles
const ROLE_ICONS = {
  CEO: '👔',
  CFO: '💰',
  CTO: '⚙️',
  CHRO: '👥',
  CSO: '📈',
  CPO_CSCO: '🔗',
  CPO: '📦',
  CISO: '🔒',
  CMO: '📣',
  CRO: '⚖️',
  CCO: '🤝',
  COO: '🏭',
  CLO: '📜',
  DEVILS_ADVOCATE: '😈',
}

function ExecutiveCard({ role, title, response, confidence, uncertainties, isExpanded, onToggle, executiveInfo, t }) {
  const info = executiveInfo[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `exec-card-${role}`
  const translations = t || TRANSLATIONS.de

  const getConfidenceClass = (conf) => {
    switch (conf?.toUpperCase()) {
      case 'HIGH': return 'high'
      case 'MEDIUM': return 'medium'
      case 'LOW': return 'low'
      default: return ''
    }
  }

  return (
    <article
      className="executive-card"
      style={{ borderLeftColor: info.color }}
      aria-labelledby={`${cardId}-title`}
    >
      <button
        className="executive-header"
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={`${cardId}-content`}
        type="button"
      >
        <div className="executive-info">
          <span className="executive-icon" aria-hidden="true">{info.icon}</span>
          <div>
            <h3 id={`${cardId}-title`}>{info.title}</h3>
            <p className="german-title">{info.german}</p>
            {confidence && (
              <span className={`confidence-badge ${getConfidenceClass(confidence)}`}>
                {confidence}
              </span>
            )}
          </div>
        </div>
        <span className="toggle-btn" aria-hidden="true">
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </span>
      </button>
      {isExpanded && (
        <div id={`${cardId}-content`} className="executive-content" role="region">
          <ReactMarkdown>{response}</ReactMarkdown>
          {uncertainties && uncertainties.length > 0 && (
            <div className="uncertainties-section">
              <h4><AlertTriangle size={16} /> {translations.keyUncertainties}</h4>
              <ul>
                {uncertainties.map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </article>
  )
}

function EvaluationCard({ role, title, evaluation, isExpanded, onToggle, executiveInfo, t }) {
  const info = executiveInfo[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `eval-card-${role}`
  const translations = t || TRANSLATIONS.de

  return (
    <article
      className="evaluation-card"
      style={{ borderLeftColor: info.color }}
      aria-labelledby={`${cardId}-title`}
    >
      <button
        className="executive-header"
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={`${cardId}-content`}
        type="button"
      >
        <div className="executive-info">
          <span className="executive-icon" aria-hidden="true">{info.icon}</span>
          <div>
            <h3 id={`${cardId}-title`}>{translations.evaluationBy} {info.title}</h3>
            <p className="german-title">{info.german}</p>
          </div>
        </div>
        <span className="toggle-btn" aria-hidden="true">
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </span>
      </button>
      {isExpanded && (
        <div id={`${cardId}-content`} className="executive-content" role="region">
          <ReactMarkdown>{evaluation}</ReactMarkdown>
        </div>
      )}
    </article>
  )
}

function DebateCard({ role, title, response, isExpanded, onToggle, executiveInfo, t }) {
  const info = executiveInfo[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `debate-card-${role}`
  const translations = t || TRANSLATIONS.de

  return (
    <article
      className="debate-card"
      style={{ borderLeftColor: info.color }}
      aria-labelledby={`${cardId}-title`}
    >
      <button
        className="executive-header"
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={`${cardId}-content`}
        type="button"
      >
        <div className="executive-info">
          <span className="executive-icon" aria-hidden="true">{info.icon}</span>
          <div>
            <h3 id={`${cardId}-title`}>{info.title} {translations.responds}</h3>
            <p className="german-title">{translations.debateResponse}</p>
          </div>
        </div>
        <span className="toggle-btn" aria-hidden="true">
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </span>
      </button>
      {isExpanded && (
        <div id={`${cardId}-content`} className="executive-content" role="region">
          <ReactMarkdown>{response}</ReactMarkdown>
        </div>
      )}
    </article>
  )
}

function RiskMatrix({ risks, t }) {
  const translations = t || TRANSLATIONS.de
  if (!risks || risks.length === 0) return null

  return (
    <div className="risk-matrix">
      <h3><Shield size={20} /> {translations.riskMatrix}</h3>
      <div className="risk-table-container">
        <table className="risk-table">
          <thead>
            <tr>
              <th>{translations.risk}</th>
              <th>{translations.category}</th>
              <th>{translations.level}</th>
              <th>{translations.owner}</th>
              <th>{translations.mitigation}</th>
            </tr>
          </thead>
          <tbody>
            {risks.map((risk, i) => (
              <tr key={risk.id || i}>
                <td className="risk-description">{risk.description}</td>
                <td><span className="risk-category-badge">{risk.category}</span></td>
                <td>
                  <span className={`risk-level-badge ${risk.risk_level || ''}`}>
                    {risk.risk_level?.toUpperCase() || 'N/A'}
                  </span>
                </td>
                <td><span className="risk-owner-badge">{risk.owner}</span></td>
                <td className="risk-mitigation">{risk.mitigation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function FileUploadZone({ files, setFiles, t }) {
  const translations = t || TRANSLATIONS.de
  const onDrop = (acceptedFiles) => {
    setFiles(prev => [...prev, ...acceptedFiles])
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    }
  })

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="file-upload-section">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''}`}
      >
        <input {...getInputProps()} />
        <Upload size={32} aria-hidden="true" />
        <p>{translations.dragDropFiles}</p>
        <span className="file-types">{translations.fileTypes}</span>
      </div>

      {files.length > 0 && (
        <div className="file-list">
          {files.map((file, index) => (
            <div key={index} className="file-item">
              <FileText size={16} aria-hidden="true" />
              <span>{file.name}</span>
              <button
                onClick={() => removeFile(index)}
                className="remove-file"
                aria-label={`${t.removeFile}: ${file.name}`}
                type="button"
              >
                <X size={14} aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function StageProgress({ currentStage, stages }) {
  const currentStageName = currentStage >= 0 && currentStage < stages.length
    ? stages[currentStage]
    : ''

  return (
    <div className="stage-progress" role="progressbar" aria-valuenow={currentStage + 1} aria-valuemin="1" aria-valuemax={stages.length}>
      <div className="sr-only" aria-live="polite">
        Currently processing: {currentStageName}
      </div>
      {stages.map((stage, index) => (
        <div
          key={index}
          className={`stage-item ${currentStage > index ? 'completed' : ''} ${currentStage === index ? 'active' : ''}`}
          aria-current={currentStage === index ? 'step' : undefined}
        >
          <div className="stage-indicator" aria-hidden="true">
            {currentStage > index ? (
              <CheckCircle2 size={20} />
            ) : currentStage === index ? (
              <Loader2 size={20} className="spinning" />
            ) : (
              <span>{index + 1}</span>
            )}
          </div>
          <span className="stage-label">{stage}</span>
        </div>
      ))}
    </div>
  )
}

function MeetingHistory({ meetings, onSelect, onDelete, currentMeetingId, t }) {
  const translations = t || TRANSLATIONS.de

  if (!meetings || meetings.length === 0) {
    return (
      <div className="meeting-history">
        <h3><History size={20} /> {translations.meetingHistory}</h3>
        <div className="empty-history">
          <History size={32} />
          <p>{translations.noPreviousMeetings}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="meeting-history">
      <h3><History size={20} /> {translations.meetingHistory}</h3>
      <div className="meeting-list">
        {meetings.slice(0, 10).map((meeting) => (
          <div
            key={meeting.id}
            className={`meeting-item ${meeting.id === currentMeetingId ? 'active' : ''}`}
          >
            <button
              onClick={() => onSelect(meeting.id)}
              className="meeting-select-btn"
              type="button"
            >
              <h4>{meeting.title}</h4>
              <p>
                {new Date(meeting.created_at).toLocaleDateString()} • {meeting.discussion_count} {translations.discussions}
              </p>
            </button>
            <button
              onClick={() => onDelete(meeting.id)}
              className="meeting-delete-btn"
              aria-label={translations.deleteMeeting}
              type="button"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function TemplateSelector({ templates, onSelect, t }) {
  const translations = t || TRANSLATIONS.de
  const [selectedCategory, setSelectedCategory] = useState('all')

  const categories = ['all', ...new Set(templates.map(tmpl => tmpl.category))]
  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(tmpl => tmpl.category === selectedCategory)

  return (
    <div className="template-selector">
      <div className="category-tabs">
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`category-tab ${selectedCategory === cat ? 'active' : ''}`}
            type="button"
          >
            {cat === 'all' ? translations.all : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>
      <div className="template-grid">
        {filteredTemplates.map(template => (
          <button
            key={template.id}
            onClick={() => onSelect(template.prompt)}
            className="template-card"
            type="button"
          >
            <h4>{template.name}</h4>
            <span className="template-category">{template.category}</span>
            <p>{template.description}</p>
          </button>
        ))}
      </div>
    </div>
  )
}

// Auth Modal Component
function AuthModal({ isOpen, onClose, onSuccess, t, initialMode = 'login' }) {
  const [mode, setMode] = useState(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    setMode(initialMode)
  }, [initialMode])

  if (!isOpen) return null

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)

    try {
      if (mode === 'login') {
        const response = await fetch(`${API_URL}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || t.loginError)
        }

        const data = await response.json()
        // Store token in localStorage for API calls
        localStorage.setItem('auth_token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        onSuccess(data.user, data.access_token)
        onClose()
      } else {
        const response = await fetch(`${API_URL}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })

        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || t.registerError)
        }

        const data = await response.json()
        if (data.access_token) {
          localStorage.setItem('auth_token', data.access_token)
          localStorage.setItem('user', JSON.stringify(data.user))
          onSuccess(data.user, data.access_token)
          onClose()
        } else {
          setMessage(t.registerSuccess)
          setMode('login')
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} type="button">
          <X size={24} />
        </button>

        <h2>{mode === 'login' ? t.loginTitle : t.registerTitle}</h2>

        {error && (
          <div className="auth-error">
            <AlertCircle size={16} />
            {error}
          </div>
        )}

        {message && (
          <div className="auth-message">
            <CheckCircle2 size={16} />
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="auth-email">{t.email}</label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="auth-password">{t.password}</label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              disabled={loading}
            />
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading ? <Loader2 size={20} className="spinning" /> : null}
            {mode === 'login' ? t.login : t.register}
          </button>
        </form>

        <div className="auth-switch">
          {mode === 'login' ? (
            <p>
              {t.noAccount}{' '}
              <button type="button" onClick={() => setMode('register')}>
                {t.register}
              </button>
            </p>
          ) : (
            <p>
              {t.hasAccount}{' '}
              <button type="button" onClick={() => setMode('login')}>
                {t.login}
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

// Limit Reached Modal
function LimitReachedModal({ isOpen, onClose, onLogin, onRegister, tier, t }) {
  if (!isOpen) return null

  const isAnonymous = tier === 'anonymous'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="limit-modal" onClick={e => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} type="button">
          <X size={24} />
        </button>

        <div className="limit-icon">
          <AlertOctagon size={48} />
        </div>

        <h2>{t.limitReachedTitle}</h2>
        <p>{isAnonymous ? t.limitReachedAnon : t.limitReachedFree}</p>

        <div className="limit-actions">
          {isAnonymous ? (
            <>
              <button className="primary-btn" onClick={onRegister} type="button">
                <User size={20} />
                {t.createAccount}
              </button>
              <button className="secondary-btn" onClick={onLogin} type="button">
                <LogIn size={20} />
                {t.login}
              </button>
            </>
          ) : (
            <button className="primary-btn" onClick={() => window.open('/upgrade', '_blank')} type="button">
              <CreditCard size={20} />
              {t.upgradeToPro}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// Usage Badge Component
function UsageBadge({ usage, user, t, onClick }) {
  if (!usage) return null

  const remaining = usage.remaining_monthly >= 0 ? usage.remaining_monthly : null
  const isUnlimited = remaining === null || remaining === -1
  const isLow = remaining !== null && remaining <= 2 && !isUnlimited

  const tierName = user?.tier || 'anonymous'
  const tierLabel = {
    anonymous: t.tierAnonymous,
    free: t.tierFree,
    pro: t.tierPro,
    enterprise: t.tierEnterprise
  }[tierName] || tierName

  return (
    <button className={`usage-badge ${isLow ? 'low' : ''}`} onClick={onClick} type="button">
      <span className="tier-label">{tierLabel}</span>
      {isUnlimited ? (
        <span className="usage-count">{t.unlimited}</span>
      ) : (
        <span className="usage-count">{remaining} {t.remaining}</span>
      )}
    </button>
  )
}

function IndustrySelector({ industries, onSelect, isLoading, t }) {
  if (isLoading) {
    return (
      <div className="industry-selector">
        <div className="industry-loading">
          <Loader2 size={48} className="spinning" />
          <p>{t.loadingIndustries}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="industry-selector">
      <div className="industry-header">
        <Building2 size={48} />
        <h1>{t.appTitle}</h1>
        <p>{t.selectIndustryDesc}</p>
      </div>
      <div className="industry-grid">
        {industries.map(industry => {
          const IconComponent = INDUSTRY_ICONS[industry.id] || Building2
          return (
            <button
              key={industry.id}
              onClick={() => onSelect(industry)}
              className="industry-card"
              type="button"
            >
              <div className="industry-icon">
                <IconComponent size={32} />
              </div>
              <h3>{industry.german_context}</h3>
              <p className="industry-german">{industry.name}</p>
              <p className="industry-description">{industry.description}</p>
            </button>
          )
        })}
      </div>
    </div>
  )
}

function App() {
  // Auth state
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user')
    return saved ? JSON.parse(saved) : null
  })
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('auth_token'))
  const [usage, setUsage] = useState(null)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authModalMode, setAuthModalMode] = useState('login')
  const [showLimitModal, setShowLimitModal] = useState(false)

  // Industry state - persisted in localStorage
  const [selectedIndustry, setSelectedIndustry] = useState(() => {
    const saved = localStorage.getItem('selectedIndustry')
    return saved ? JSON.parse(saved) : null
  })
  const [industries, setIndustries] = useState([])
  const [industriesLoading, setIndustriesLoading] = useState(true)
  const [executiveInfo, setExecutiveInfo] = useState(DEFAULT_EXECUTIVE_INFO)

  // Main app state
  const [situation, setSituation] = useState('')
  const [files, setFiles] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentStage, setCurrentStage] = useState(-1)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [expandedCards, setExpandedCards] = useState({})
  const [meetings, setMeetings] = useState([])
  const [currentMeeting, setCurrentMeeting] = useState(null)
  const [templates, setTemplates] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [showTemplates, setShowTemplates] = useState(false)
  const [includeDebate, setIncludeDebate] = useState(true)
  const [includeRiskMatrix, setIncludeRiskMatrix] = useState(true)
  const resultRef = useRef(null)

  const stages = [
    t.stagePerspectives,
    t.stageEvaluation,
    t.stageDebate,
    t.stageRiskAnalysis,
    t.stageSynthesis
  ]

  // Auth functions
  const handleAuthSuccess = (userData, token) => {
    setUser(userData)
    setAuthToken(token)
    fetchUsage(token)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    setUser(null)
    setAuthToken(null)
    setUsage(null)
    fetchUsage(null) // Fetch anonymous usage
  }

  const fetchUsage = useCallback(async (token = authToken) => {
    try {
      const headers = {}
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      const response = await fetch(`${API_URL}/api/usage`, { headers })
      if (response.ok) {
        const data = await response.json()
        setUsage(data)
      }
    } catch (err) {
      console.error('Failed to fetch usage:', err)
    }
  }, [authToken])

  const openAuthModal = (mode = 'login') => {
    setAuthModalMode(mode)
    setShowAuthModal(true)
  }

  // Fetch usage on mount and when auth changes
  useEffect(() => {
    fetchUsage()
  }, [fetchUsage])

  // Fetch industries on mount
  useEffect(() => {
    fetchIndustries()
  }, [])

  // When industry changes, save to localStorage and fetch industry-specific data
  useEffect(() => {
    if (selectedIndustry) {
      localStorage.setItem('selectedIndustry', JSON.stringify(selectedIndustry))
      fetchIndustryExecutives(selectedIndustry.id)
      fetchTemplates(selectedIndustry.id)
      fetchMeetings()
    }
  }, [selectedIndustry])

  useEffect(() => {
    if (results && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [results])

  const fetchIndustries = async () => {
    setIndustriesLoading(true)
    try {
      const response = await fetch(`${API_URL}/api/industries`)
      const data = await response.json()
      setIndustries(data)
    } catch (err) {
      console.error('Failed to fetch industries:', err)
    } finally {
      setIndustriesLoading(false)
    }
  }

  const fetchIndustryExecutives = async (industryId) => {
    try {
      const response = await fetch(`${API_URL}/api/industries/${industryId}/executives`)
      const data = await response.json()
      // Transform backend data to frontend format with colors and icons
      const transformed = {}
      for (const [roleKey, roleData] of Object.entries(data)) {
        transformed[roleKey] = {
          title: roleData.title,
          german: roleData.german || '',
          color: ROLE_COLORS[roleKey] || '#666',
          icon: ROLE_ICONS[roleKey] || '👤'
        }
      }
      setExecutiveInfo(transformed)
    } catch (err) {
      console.error('Failed to fetch executives:', err)
      setExecutiveInfo(DEFAULT_EXECUTIVE_INFO)
    }
  }

  const handleIndustrySelect = (industry) => {
    setSelectedIndustry(industry)
    // Reset meeting state when changing industry
    setCurrentMeeting(null)
    setResults(null)
    setSituation('')
  }

  const changeIndustry = () => {
    setSelectedIndustry(null)
    localStorage.removeItem('selectedIndustry')
    setCurrentMeeting(null)
    setResults(null)
    setSituation('')
  }

  const fetchMeetings = async () => {
    try {
      const response = await fetch(`${API_URL}/api/meetings`)
      const data = await response.json()
      // Filter meetings by current industry if selected
      const filtered = selectedIndustry
        ? data.filter(m => m.industry === selectedIndustry.id || !m.industry)
        : data
      setMeetings(filtered)
    } catch (err) {
      console.error('Failed to fetch meetings:', err)
    }
  }

  const fetchTemplates = async (industryId) => {
    try {
      // Use industry-specific templates if available
      const url = industryId
        ? `${API_URL}/api/industries/${industryId}/templates`
        : `${API_URL}/api/templates`
      const response = await fetch(url)
      const data = await response.json()
      setTemplates(data)
    } catch (err) {
      console.error('Failed to fetch templates:', err)
    }
  }

  const createMeeting = async () => {
    try {
      const response = await fetch(`${API_URL}/api/meetings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          industry: selectedIndustry?.id || 'manufacturing'
        })
      })
      const data = await response.json()
      setCurrentMeeting(data)
      return data.id
    } catch (err) {
      setError(t.failedCreateMeeting)
      return null
    }
  }

  const loadMeeting = async (meetingId) => {
    try {
      const response = await fetch(`${API_URL}/api/meetings/${meetingId}`)
      const data = await response.json()
      setCurrentMeeting(data)

      // If there are discussions, show the last one as results
      if (data.discussions && data.discussions.length > 0) {
        const lastBoard = data.discussions.filter(d => d.role === 'board').pop()
        if (lastBoard) {
          setResults({
            stage1_perspectives: lastBoard.stage1_perspectives,
            stage2_evaluations: lastBoard.stage2_evaluations,
            stage2_5_debate: lastBoard.debate_results,
            stage3_synthesis: lastBoard.stage3_synthesis,
            risk_matrix: lastBoard.risk_matrix,
            metadata: {}
          })
        }
      }
      setShowHistory(false)
    } catch (err) {
      setError(t.failedLoadMeeting)
    }
  }

  const deleteMeeting = async (meetingId) => {
    if (!confirm(t.confirmDeleteMeeting)) return

    try {
      await fetch(`${API_URL}/api/meetings/${meetingId}`, { method: 'DELETE' })
      fetchMeetings()
      if (currentMeeting?.id === meetingId) {
        setCurrentMeeting(null)
        setResults(null)
      }
    } catch (err) {
      setError(t.failedDeleteMeeting)
    }
  }

  const toggleCard = (key) => {
    setExpandedCards(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const expandAllCards = () => {
    const allKeys = {}
    if (results?.stage1_perspectives) {
      results.stage1_perspectives.forEach(p => allKeys[`s1-${p.role}`] = true)
    }
    if (results?.stage2_evaluations) {
      results.stage2_evaluations.forEach(e => allKeys[`s2-${e.role}`] = true)
    }
    if (results?.stage2_5_debate) {
      results.stage2_5_debate.forEach(d => allKeys[`debate-${d.role}`] = true)
    }
    setExpandedCards(allKeys)
  }

  const collapseAllCards = () => {
    setExpandedCards({})
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      alert(t.copiedToClipboard)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const exportMeeting = async (format = 'markdown') => {
    if (!currentMeeting) return

    try {
      const response = await fetch(`${API_URL}/api/meetings/${currentMeeting.id}/export?format=${format}`)
      if (format === 'markdown') {
        const text = await response.text()
        const blob = new Blob([text], { type: 'text/markdown' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${currentMeeting.title || 'meeting'}.md`
        a.click()
        URL.revokeObjectURL(url)
      } else {
        const data = await response.json()
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${currentMeeting.title || 'meeting'}.json`
        a.click()
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      setError(t.failedExportMeeting)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!situation.trim()) return

    setIsLoading(true)
    setError(null)
    setResults(null)
    setCurrentStage(0)

    try {
      // Create a new meeting
      const meetingId = await createMeeting()
      if (!meetingId) return

      // Prepare the situation with file contents if any
      let fullSituation = situation

      if (files.length > 0) {
        const fileContents = await Promise.all(
          files.map(async (file) => {
            const text = await file.text()
            return `\n\n--- Document: ${file.name} ---\n${text}`
          })
        )
        fullSituation += '\n\nAttached Documents:' + fileContents.join('')
      }

      // Build headers with auth token if available
      const headers = { 'Content-Type': 'application/json' }
      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`
      }

      // Use streaming endpoint
      const response = await fetch(`${API_URL}/api/meetings/${meetingId}/discuss/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          content: fullSituation,
          include_debate: includeDebate,
          include_risk_matrix: includeRiskMatrix
        })
      })

      // Handle rate limit exceeded
      if (response.status === 429) {
        const errorData = await response.json()
        setError(errorData.detail?.message || t.limitReached)
        setShowLimitModal(true)
        setIsLoading(false)
        return
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Request failed')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let stage1Data = null
      let stage2Data = null
      let stage2_5Data = null
      let stage3Data = null
      let riskMatrixData = null
      let metadata = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              switch (data.type) {
                case 'usage':
                  // Update usage info from stream
                  setUsage(data.data)
                  break
                case 'stage1_start':
                  setCurrentStage(0)
                  break
                case 'stage1_complete':
                  stage1Data = data.data
                  setCurrentStage(1)
                  break
                case 'stage2_start':
                  setCurrentStage(1)
                  break
                case 'stage2_complete':
                  stage2Data = data.data
                  metadata = data.metadata
                  setCurrentStage(2)
                  break
                case 'stage2_5_start':
                  setCurrentStage(2)
                  break
                case 'stage2_5_complete':
                  stage2_5Data = data.data
                  setCurrentStage(3)
                  break
                case 'risk_matrix_start':
                  setCurrentStage(3)
                  break
                case 'risk_matrix_complete':
                  riskMatrixData = data.data
                  setCurrentStage(4)
                  break
                case 'stage3_start':
                  setCurrentStage(4)
                  break
                case 'stage3_complete':
                  stage3Data = data.data
                  break
                case 'complete':
                  setResults({
                    stage1_perspectives: stage1Data,
                    stage2_evaluations: stage2Data,
                    stage2_5_debate: stage2_5Data,
                    stage3_synthesis: stage3Data,
                    risk_matrix: riskMatrixData,
                    metadata
                  })
                  fetchMeetings()
                  break
                case 'error':
                  setError(data.message)
                  break
              }
            } catch {
              // Ignore parse errors for incomplete chunks
            }
          }
        }
      }
    } catch (err) {
      setError(`${t.failedSubmit}: ${err.message}`)
    } finally {
      setIsLoading(false)
      setCurrentStage(-1)
      // Refresh usage after request
      fetchUsage()
    }
  }

  // Show industry selector if no industry is selected
  if (!selectedIndustry) {
    return (
      <div className="app industry-select-mode">
        <IndustrySelector
          industries={industries}
          onSelect={handleIndustrySelect}
          isLoading={industriesLoading}
          t={t}
        />
      </div>
    )
  }

  const IndustryIcon = INDUSTRY_ICONS[selectedIndustry.id] || Building2

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <IndustryIcon size={32} aria-hidden="true" />
          <div>
            <h1>{t.appTitle}</h1>
            <p>{selectedIndustry.german_context}</p>
          </div>
        </div>
        <div className="header-actions">
          {/* Usage Badge */}
          <UsageBadge
            usage={usage}
            user={user}
            t={t}
            onClick={() => !user && openAuthModal('register')}
          />

          {/* Auth buttons */}
          {user ? (
            <button
              onClick={handleLogout}
              className="header-btn"
              type="button"
              aria-label={t.logout}
            >
              <LogOut size={20} />
              <span className="btn-label">{t.logout}</span>
            </button>
          ) : (
            <button
              onClick={() => openAuthModal('login')}
              className="header-btn auth-btn"
              type="button"
              aria-label={t.login}
            >
              <LogIn size={20} />
              <span className="btn-label">{t.login}</span>
            </button>
          )}

          <button
            onClick={changeIndustry}
            className="header-btn change-industry-btn"
            type="button"
            aria-label={t.changeIndustry}
          >
            <ArrowLeft size={20} />
            <span className="btn-label">{t.changeIndustry}</span>
          </button>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`header-btn ${showHistory ? 'active' : ''}`}
            type="button"
            aria-label={t.history}
          >
            <History size={20} />
            <span className="btn-label">{t.history}</span>
          </button>
          {currentMeeting && (
            <button
              onClick={() => exportMeeting('markdown')}
              className="header-btn"
              type="button"
              aria-label={t.export}
            >
              <Download size={20} />
              <span className="btn-label">{t.export}</span>
            </button>
          )}
        </div>
      </header>

      <div className="main-container">
        {showHistory && (
          <aside className="sidebar">
            <MeetingHistory
              meetings={meetings}
              onSelect={loadMeeting}
              onDelete={deleteMeeting}
              currentMeetingId={currentMeeting?.id}
              t={t}
            />
          </aside>
        )}

        <main className="main">
          <div className="input-section">
            <div className="section-header">
              <MessageSquare size={24} aria-hidden="true" />
              <h2>{t.presentSituation}</h2>
              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className={`template-toggle ${showTemplates ? 'active' : ''}`}
                type="button"
              >
                <Lightbulb size={16} />
                {t.templates}
              </button>
            </div>

            {showTemplates && templates.length > 0 && (
              <TemplateSelector
                templates={templates}
                onSelect={(prompt) => {
                  setSituation(prompt)
                  setShowTemplates(false)
                }}
                t={t}
              />
            )}

            <form onSubmit={handleSubmit}>
              <label htmlFor="situation-input" className="sr-only">
                {t.presentSituation}
              </label>
              <textarea
                id="situation-input"
                value={situation}
                onChange={(e) => setSituation(e.target.value)}
                placeholder={t.situationPlaceholder}
                rows={6}
                disabled={isLoading}
                aria-describedby="situation-help"
              />
              <p id="situation-help" className="sr-only">
                {t.presentSituation}
              </p>

              <FileUploadZone files={files} setFiles={setFiles} t={t} />

              <div className="options-row">
                <label className="option-checkbox">
                  <input
                    type="checkbox"
                    checked={includeDebate}
                    onChange={(e) => setIncludeDebate(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>{t.includeDebate}</span>
                </label>
                <label className="option-checkbox">
                  <input
                    type="checkbox"
                    checked={includeRiskMatrix}
                    onChange={(e) => setIncludeRiskMatrix(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>{t.generateRiskMatrix}</span>
                </label>
              </div>

              <button
                type="submit"
                className="submit-btn"
                disabled={isLoading || !situation.trim()}
              >
                {isLoading ? (
                  <>
                    <Loader2 size={20} className="spinning" aria-hidden="true" />
                    {t.consultingBoard}
                  </>
                ) : (
                  <>
                    <Send size={20} aria-hidden="true" />
                    {t.conveneBoard}
                  </>
                )}
              </button>
            </form>

            {isLoading && (
              <StageProgress currentStage={currentStage} stages={stages} />
            )}

            {error && (
              <div className="error-message" role="alert">
                <AlertCircle size={20} aria-hidden="true" />
                {error}
              </div>
            )}
          </div>

          {results && (
            <div className="results-section" ref={resultRef}>
              <div className="results-controls">
                <button onClick={expandAllCards} className="control-btn" type="button">
                  {t.expandAll}
                </button>
                <button onClick={collapseAllCards} className="control-btn" type="button">
                  {t.collapseAll}
                </button>
                {results.stage3_synthesis?.response && (
                  <button
                    onClick={() => copyToClipboard(results.stage3_synthesis.response)}
                    className="control-btn"
                    type="button"
                  >
                    <Copy size={16} /> {t.copySynthesis}
                  </button>
                )}
              </div>

              {/* Stage 1: Individual Perspectives */}
              <div className="stage-section">
                <div className="stage-header">
                  <Users size={24} aria-hidden="true" />
                  <h2>{t.stage1Title}</h2>
                </div>
                <div className="cards-grid">
                  {results.stage1_perspectives?.map((perspective) => (
                    <ExecutiveCard
                      key={perspective.role}
                      role={perspective.role}
                      title={perspective.title}
                      response={perspective.response}
                      confidence={perspective.confidence}
                      uncertainties={perspective.uncertainties}
                      isExpanded={expandedCards[`s1-${perspective.role}`]}
                      onToggle={() => toggleCard(`s1-${perspective.role}`)}
                      executiveInfo={executiveInfo}
                      t={t}
                    />
                  ))}
                </div>
              </div>

              {/* Stage 2: Cross-Evaluations */}
              <div className="stage-section">
                <div className="stage-header">
                  <MessageSquare size={24} aria-hidden="true" />
                  <h2>{t.stage2Title}</h2>
                </div>

                {results.metadata?.aggregate_rankings && (
                  <div className="rankings-summary">
                    <h3>{t.aggregateRankings}</h3>
                    <div className="rankings-list">
                      {results.metadata.aggregate_rankings.map((ranking, index) => (
                        <div key={ranking.role} className="ranking-item">
                          <span className="rank">#{index + 1}</span>
                          <span className="rank-title">{ranking.title}</span>
                          <span className="rank-score">{t.avg}: {ranking.average_rank.toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="cards-grid">
                  {results.stage2_evaluations?.map((evaluation) => (
                    <EvaluationCard
                      key={evaluation.role}
                      role={evaluation.role}
                      title={evaluation.title}
                      evaluation={evaluation.evaluation}
                      isExpanded={expandedCards[`s2-${evaluation.role}`]}
                      onToggle={() => toggleCard(`s2-${evaluation.role}`)}
                      executiveInfo={executiveInfo}
                      t={t}
                    />
                  ))}
                </div>
              </div>

              {/* Stage 2.5: Debate */}
              {results.stage2_5_debate && results.stage2_5_debate.length > 0 && (
                <div className="stage-section debate-section">
                  <div className="stage-header">
                    <RefreshCw size={24} aria-hidden="true" />
                    <h2>{t.stage2_5Title}</h2>
                  </div>
                  <div className="cards-grid">
                    {results.stage2_5_debate.map((debate) => (
                      <DebateCard
                        key={debate.role}
                        role={debate.role}
                        title={debate.title}
                        response={debate.response}
                        isExpanded={expandedCards[`debate-${debate.role}`]}
                        onToggle={() => toggleCard(`debate-${debate.role}`)}
                        executiveInfo={executiveInfo}
                        t={t}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Risk Matrix */}
              {results.risk_matrix?.risks && results.risk_matrix.risks.length > 0 && (
                <div className="stage-section risk-section">
                  <RiskMatrix risks={results.risk_matrix.risks} t={t} />
                </div>
              )}

              {/* Stage 3: Final Synthesis */}
              <div className="stage-section synthesis-section">
                <div className="stage-header">
                  <CheckCircle2 size={24} aria-hidden="true" />
                  <h2>{t.stage3Title}</h2>
                </div>
                <div className="synthesis-content">
                  <ReactMarkdown>{results.stage3_synthesis?.response}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>

      <footer className="footer">
        <p>{t.footerVersion}</p>
        <p className="footer-features">
          {t.footerFeatures}
        </p>
      </footer>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
        t={t}
        initialMode={authModalMode}
      />

      {/* Limit Reached Modal */}
      <LimitReachedModal
        isOpen={showLimitModal}
        onClose={() => setShowLimitModal(false)}
        onLogin={() => {
          setShowLimitModal(false)
          openAuthModal('login')
        }}
        onRegister={() => {
          setShowLimitModal(false)
          openAuthModal('register')
        }}
        tier={usage?.tier || 'anonymous'}
        t={t}
      />
    </div>
  )
}

export default App
