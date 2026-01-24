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
  AlertCircle
} from 'lucide-react'
import './App.css'

const EXECUTIVE_INFO = {
  CEO: { title: 'Chief Executive Officer', german: 'Vorstandsvorsitzender', color: '#2563eb', icon: '👔' },
  CFO: { title: 'Chief Financial Officer', german: 'Finanzvorstand', color: '#059669', icon: '💰' },
  CTO: { title: 'Chief Technology Officer', german: 'Technischer Vorstand', color: '#7c3aed', icon: '⚙️' },
  CHRO: { title: 'Chief Human Resources Officer', german: 'Personalvorstand', color: '#db2777', icon: '👥' },
  CSO: { title: 'Chief Sales Officer', german: 'Vertriebsvorstand', color: '#ea580c', icon: '📈' },
  CPO_CSCO: { title: 'Chief Purchasing & Supply Chain Officer', german: 'Einkaufs- und Supply Chain Vorstand', color: '#0891b2', icon: '🔗' },
}

function ExecutiveCard({ role, title, response, isExpanded, onToggle }) {
  const info = EXECUTIVE_INFO[role] || { title: role, german: '', color: '#666', icon: '👤' }
  const cardId = `exec-card-${role}`

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
        <Upload size={32} />
        <p>Drag & drop documents here, or click to select</p>
        <span className="file-types">PDF, DOC, DOCX, TXT, CSV, XLS, XLSX</span>
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
  const resultRef = useRef(null)

  const stages = [
    'Collecting Perspectives',
    'Cross-Evaluation',
    'Final Synthesis'
  ]

  useEffect(() => {
    fetchMeetings()
  }, [])

  useEffect(() => {
    if (results && resultRef.current) {
      resultRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [results])

  const fetchMeetings = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/meetings')
      const data = await response.json()
      setMeetings(data)
    } catch (err) {
      console.error('Failed to fetch meetings:', err)
    }
  }

  const createMeeting = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/meetings', {
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
    setExpandedCards(allKeys)
  }

  const collapseAllCards = () => {
    setExpandedCards({})
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
      const response = await fetch(`http://localhost:8001/api/meetings/${meetingId}/discuss/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: fullSituation })
      })

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let stage1Data = null
      let stage2Data = null
      let stage3Data = null
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
                case 'stage3_start':
                  setCurrentStage(2)
                  break
                case 'stage3_complete':
                  stage3Data = data.data
                  setCurrentStage(3)
                  break
                case 'complete':
                  setResults({
                    stage1_perspectives: stage1Data,
                    stage2_evaluations: stage2Data,
                    stage3_synthesis: stage3Data,
                    metadata
                  })
                  fetchMeetings()
                  break
                case 'error':
                  setError(data.message)
                  break
              }
            } catch (err) {
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
          <Building2 size={32} />
          <div>
            <h1>Executive Board Council</h1>
            <p>German Production Company Decision Support</p>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="input-section">
          <div className="section-header">
            <MessageSquare size={24} />
            <h2>Present a Business Situation</h2>
          </div>

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

            <button
              type="submit"
              className="submit-btn"
              disabled={isLoading || !situation.trim()}
            >
              {isLoading ? (
                <>
                  <Loader2 size={20} className="spinning" />
                  Consulting the Board...
                </>
              ) : (
                <>
                  <Send size={20} />
                  Convene Executive Board
                </>
              )}
            </button>
          </form>

          {isLoading && (
            <StageProgress currentStage={currentStage} stages={stages} />
          )}

          {error && (
            <div className="error-message">
              <AlertCircle size={20} />
              {error}
            </div>
          )}
        </div>

        {results && (
          <div className="results-section" ref={resultRef}>
            <div className="results-controls">
              <button onClick={expandAllCards} className="control-btn">Expand All</button>
              <button onClick={collapseAllCards} className="control-btn">Collapse All</button>
            </div>

            {/* Stage 1: Individual Perspectives */}
            <div className="stage-section">
              <div className="stage-header">
                <Users size={24} />
                <h2>Stage 1: Executive Perspectives</h2>
              </div>
              <div className="cards-grid">
                {results.stage1_perspectives?.map((perspective) => (
                  <ExecutiveCard
                    key={perspective.role}
                    role={perspective.role}
                    title={perspective.title}
                    response={perspective.response}
                    isExpanded={expandedCards[`s1-${perspective.role}`]}
                    onToggle={() => toggleCard(`s1-${perspective.role}`)}
                  />
                ))}
              </div>
            </div>

            {/* Stage 2: Cross-Evaluations */}
            <div className="stage-section">
              <div className="stage-header">
                <MessageSquare size={24} />
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

            {/* Stage 3: Final Synthesis */}
            <div className="stage-section synthesis-section">
              <div className="stage-header">
                <CheckCircle2 size={24} />
                <h2>Stage 3: Council Speaker's Recommendation</h2>
              </div>
              <div className="synthesis-content">
                <ReactMarkdown>{results.stage3_synthesis?.response}</ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="footer">
        <p>Executive Board Council - Powered by Multiple LLMs via OpenRouter</p>
      </footer>
    </div>
  )
}

export default App
