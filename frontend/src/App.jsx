import { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import { useDropzone } from 'react-dropzone'
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
  Trash2
} from 'lucide-react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const EXECUTIVE_INFO = {
  CEO: { title: 'Chief Executive Officer', german: 'Vorstandsvorsitzender', color: '#2563eb', icon: '👔' },
  CFO: { title: 'Chief Financial Officer', german: 'Finanzvorstand', color: '#059669', icon: '💰' },
  CTO: { title: 'Chief Technology Officer', german: 'Technischer Vorstand', color: '#7c3aed', icon: '⚙️' },
  CHRO: { title: 'Chief Human Resources Officer', german: 'Personalvorstand', color: '#db2777', icon: '👥' },
  CSO: { title: 'Chief Sales Officer', german: 'Vertriebsvorstand', color: '#ea580c', icon: '📈' },
  CPO_CSCO: { title: 'Chief Purchasing & Supply Chain Officer', german: 'Einkaufs- und Supply Chain Vorstand', color: '#0891b2', icon: '🔗' },
  DEVILS_ADVOCATE: { title: "Devil's Advocate", german: 'Advocatus Diaboli', color: '#dc2626', icon: '😈' },
}

function ExecutiveCard({ role, title, response, confidence, uncertainties, isExpanded, onToggle }) {
  const info = EXECUTIVE_INFO[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `exec-card-${role}`

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
              <h4><AlertTriangle size={16} /> Key Uncertainties</h4>
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

function EvaluationCard({ role, title, evaluation, isExpanded, onToggle }) {
  const info = EXECUTIVE_INFO[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `eval-card-${role}`

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
            <h3 id={`${cardId}-title`}>Evaluation by {info.title}</h3>
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

function DebateCard({ role, title, response, isExpanded, onToggle }) {
  const info = EXECUTIVE_INFO[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `debate-card-${role}`

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
            <h3 id={`${cardId}-title`}>{info.title} responds</h3>
            <p className="german-title">Debate Response</p>
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

function RiskMatrix({ risks }) {
  if (!risks || risks.length === 0) return null

  return (
    <div className="risk-matrix">
      <h3><Shield size={20} /> Risk Matrix</h3>
      <div className="risk-table-container">
        <table className="risk-table">
          <thead>
            <tr>
              <th>Risk</th>
              <th>Category</th>
              <th>Level</th>
              <th>Owner</th>
              <th>Mitigation</th>
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

function FileUploadZone({ files, setFiles }) {
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
        <p>Drag & drop documents here, or click to select</p>
        <span className="file-types">PDF, DOC, DOCX, TXT, CSV, XLS, XLSX (max 5MB each)</span>
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
                aria-label={`Remove ${file.name}`}
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
    : 'Processing'

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

function MeetingHistory({ meetings, onSelect, onDelete, currentMeetingId }) {
  if (!meetings || meetings.length === 0) {
    return (
      <div className="meeting-history">
        <h3><History size={20} /> Meeting History</h3>
        <div className="empty-history">
          <History size={32} />
          <p>No previous meetings</p>
        </div>
      </div>
    )
  }

  return (
    <div className="meeting-history">
      <h3><History size={20} /> Meeting History</h3>
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
                {new Date(meeting.created_at).toLocaleDateString()} • {meeting.discussion_count} discussion(s)
              </p>
            </button>
            <button
              onClick={() => onDelete(meeting.id)}
              className="meeting-delete-btn"
              aria-label={`Delete ${meeting.title}`}
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

function TemplateSelector({ templates, onSelect }) {
  const [selectedCategory, setSelectedCategory] = useState('all')

  const categories = ['all', ...new Set(templates.map(t => t.category))]
  const filteredTemplates = selectedCategory === 'all'
    ? templates
    : templates.filter(t => t.category === selectedCategory)

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
            {cat.charAt(0).toUpperCase() + cat.slice(1)}
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

function App() {
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
    'Perspectives',
    'Evaluation',
    'Debate',
    'Risk Analysis',
    'Synthesis'
  ]

  useEffect(() => {
    fetchMeetings()
    fetchTemplates()
  }, [])

  useEffect(() => {
    if (results && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [results])

  const fetchMeetings = async () => {
    try {
      const response = await fetch(`${API_URL}/api/meetings`)
      const data = await response.json()
      setMeetings(data)
    } catch (err) {
      console.error('Failed to fetch meetings:', err)
    }
  }

  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${API_URL}/api/templates`)
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
        body: JSON.stringify({})
      })
      const data = await response.json()
      setCurrentMeeting(data)
      return data.id
    } catch (err) {
      setError('Failed to create meeting')
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
      setError('Failed to load meeting')
    }
  }

  const deleteMeeting = async (meetingId) => {
    if (!confirm('Delete this meeting?')) return

    try {
      await fetch(`${API_URL}/api/meetings/${meetingId}`, { method: 'DELETE' })
      fetchMeetings()
      if (currentMeeting?.id === meetingId) {
        setCurrentMeeting(null)
        setResults(null)
      }
    } catch (err) {
      setError('Failed to delete meeting')
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
      alert('Copied to clipboard!')
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
      setError('Failed to export meeting')
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

      // Use streaming endpoint
      const response = await fetch(`${API_URL}/api/meetings/${meetingId}/discuss/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: fullSituation,
          include_debate: includeDebate,
          include_risk_matrix: includeRiskMatrix
        })
      })

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
      setError(`Failed to submit: ${err.message}`)
    } finally {
      setIsLoading(false)
      setCurrentStage(-1)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <Building2 size={32} aria-hidden="true" />
          <div>
            <h1>Executive Board Council</h1>
            <p>German Production Company Decision Support</p>
          </div>
        </div>
        <div className="header-actions">
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`header-btn ${showHistory ? 'active' : ''}`}
            type="button"
            aria-label="Toggle meeting history"
          >
            <History size={20} />
            <span className="btn-label">History</span>
          </button>
          {currentMeeting && (
            <button
              onClick={() => exportMeeting('markdown')}
              className="header-btn"
              type="button"
              aria-label="Export meeting"
            >
              <Download size={20} />
              <span className="btn-label">Export</span>
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
            />
          </aside>
        )}

        <main className="main">
          <div className="input-section">
            <div className="section-header">
              <MessageSquare size={24} aria-hidden="true" />
              <h2>Present a Business Situation</h2>
              <button
                onClick={() => setShowTemplates(!showTemplates)}
                className={`template-toggle ${showTemplates ? 'active' : ''}`}
                type="button"
              >
                <Lightbulb size={16} />
                Templates
              </button>
            </div>

            {showTemplates && templates.length > 0 && (
              <TemplateSelector
                templates={templates}
                onSelect={(prompt) => {
                  setSituation(prompt)
                  setShowTemplates(false)
                }}
              />
            )}

            <form onSubmit={handleSubmit}>
              <label htmlFor="situation-input" className="sr-only">
                Business Situation Description
              </label>
              <textarea
                id="situation-input"
                value={situation}
                onChange={(e) => setSituation(e.target.value)}
                placeholder="Describe the business situation, challenge, or decision you need guidance on...

Example: We are considering expanding our production capacity by building a new factory in Eastern Europe. What factors should we consider?"
                rows={6}
                disabled={isLoading}
                aria-describedby="situation-help"
              />
              <p id="situation-help" className="sr-only">
                Enter your business situation or challenge. The executive board will analyze it from multiple perspectives.
              </p>

              <FileUploadZone files={files} setFiles={setFiles} />

              <div className="options-row">
                <label className="option-checkbox">
                  <input
                    type="checkbox"
                    checked={includeDebate}
                    onChange={(e) => setIncludeDebate(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>Include Debate Stage</span>
                </label>
                <label className="option-checkbox">
                  <input
                    type="checkbox"
                    checked={includeRiskMatrix}
                    onChange={(e) => setIncludeRiskMatrix(e.target.checked)}
                    disabled={isLoading}
                  />
                  <span>Generate Risk Matrix</span>
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
                    Consulting the Board...
                  </>
                ) : (
                  <>
                    <Send size={20} aria-hidden="true" />
                    Convene Executive Board
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
                  Expand All
                </button>
                <button onClick={collapseAllCards} className="control-btn" type="button">
                  Collapse All
                </button>
                {results.stage3_synthesis?.response && (
                  <button
                    onClick={() => copyToClipboard(results.stage3_synthesis.response)}
                    className="control-btn"
                    type="button"
                  >
                    <Copy size={16} /> Copy Synthesis
                  </button>
                )}
              </div>

              {/* Stage 1: Individual Perspectives */}
              <div className="stage-section">
                <div className="stage-header">
                  <Users size={24} aria-hidden="true" />
                  <h2>Stage 1: Executive Perspectives</h2>
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
                    />
                  ))}
                </div>
              </div>

              {/* Stage 2: Cross-Evaluations */}
              <div className="stage-section">
                <div className="stage-header">
                  <MessageSquare size={24} aria-hidden="true" />
                  <h2>Stage 2: Cross-Evaluations</h2>
                </div>

                {results.metadata?.aggregate_rankings && (
                  <div className="rankings-summary">
                    <h3>Aggregate Rankings</h3>
                    <div className="rankings-list">
                      {results.metadata.aggregate_rankings.map((ranking, index) => (
                        <div key={ranking.role} className="ranking-item">
                          <span className="rank">#{index + 1}</span>
                          <span className="rank-title">{ranking.title}</span>
                          <span className="rank-score">Avg: {ranking.average_rank.toFixed(2)}</span>
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
                    />
                  ))}
                </div>
              </div>

              {/* Stage 2.5: Debate */}
              {results.stage2_5_debate && results.stage2_5_debate.length > 0 && (
                <div className="stage-section debate-section">
                  <div className="stage-header">
                    <RefreshCw size={24} aria-hidden="true" />
                    <h2>Stage 2.5: Debate Responses</h2>
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
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Risk Matrix */}
              {results.risk_matrix?.risks && results.risk_matrix.risks.length > 0 && (
                <div className="stage-section risk-section">
                  <RiskMatrix risks={results.risk_matrix.risks} />
                </div>
              )}

              {/* Stage 3: Final Synthesis */}
              <div className="stage-section synthesis-section">
                <div className="stage-header">
                  <CheckCircle2 size={24} aria-hidden="true" />
                  <h2>Stage 3: Council Speaker's Recommendation</h2>
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
        <p>Executive Board Council v2.0 - Powered by Multiple LLMs via OpenRouter</p>
        <p className="footer-features">
          Features: Devil's Advocate • Debate Stage • Risk Matrix • Confidence Scores • Scenario Comparison
        </p>
      </footer>
    </div>
  )
}

export default App
