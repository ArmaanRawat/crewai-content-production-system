import { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [docsContent, setDocsContent] = useState('');
  const [logs, setLogs] = useState([]);
  const [autoscroll, setAutoscroll] = useState(true);
  const [apiOnline, setApiOnline] = useState(false);

  // Form State
  const [topic, setTopic] = useState('');
  const [tone, setTone] = useState('professional');
  const [wordCount, setWordCount] = useState(800);
  const [audience, setAudience] = useState('general readers');
  const [seoKeywords, setSeoKeywords] = useState('');
  const [referenceDocs, setReferenceDocs] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [formMessage, setFormMessage] = useState({ type: '', text: '' });

  const consoleEndRef = useRef(null);

  const API_BASE = 'http://localhost:8000/api/v1';

  // 1. Check API Health on load
  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        setApiOnline(true);
      } else {
        setApiOnline(false);
      }
    } catch (e) {
      setApiOnline(false);
    }
  };

  // 2. Fetch Jobs List
  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data);
      }
    } catch (e) {
      console.error("Failed to fetch jobs list", e);
    }
  };

  // 3. Fetch Documentation
  const fetchDocs = async () => {
    try {
      const res = await fetch(`${API_BASE}/docs`);
      if (res.ok) {
        const data = await res.json();
        setDocsContent(data.content);
      }
    } catch (e) {
      console.error("Failed to fetch documentation", e);
    }
  };

  // 4. Manually trigger doc generation
  const handleRegenerateDocs = async () => {
    try {
      const res = await fetch(`${API_BASE}/docs/generate`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setDocsContent(data.content);
        alert("Technical documentation regenerated successfully!");
      }
    } catch (e) {
      alert("Failed to regenerate documentation: " + e.message);
    }
  };

  // Initial loads and interval checkups
  useEffect(() => {
    checkHealth();
    fetchJobs();

    const healthInterval = setInterval(checkHealth, 10000);
    const jobsInterval = setInterval(fetchJobs, 3000);

    return () => {
      clearInterval(healthInterval);
      clearInterval(jobsInterval);
    };
  }, []);

  // Fetch docs whenever tab switches to docs
  useEffect(() => {
    if (activeTab === 'docs') {
      fetchDocs();
    }
  }, [activeTab]);

  // Connect to Real-time SSE Logs Stream
  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/logs/stream`);
    
    eventSource.onmessage = (event) => {
      setLogs((prev) => {
        // Keep logs capped at latest 500 lines to preserve DOM performance
        const updated = [...prev, event.data];
        if (updated.length > 500) {
          return updated.slice(updated.length - 500);
        }
        return updated;
      });
    };

    eventSource.onerror = (e) => {
      console.error("SSE Connection Error", e);
    };

    return () => {
      eventSource.close();
    };
  }, []);

  // Autoscroll logs terminal
  useEffect(() => {
    if (autoscroll && consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoscroll]);

  // Handle article creation request
  const handleSubmitBrief = async (e) => {
    e.preventDefault();
    if (!topic || topic.trim().length < 5) {
      setFormMessage({ type: 'error', text: 'Topic must be at least 5 characters long.' });
      return;
    }

    setIsGenerating(true);
    setFormMessage({ type: 'info', text: 'Content brief submitted. Initiating research crew...' });
    setActiveTab('logs'); // Auto-switch to logs so they can watch progress!

    try {
      const payload = {
        topic,
        tone,
        word_count: Number(wordCount),
        audience,
        seo_keywords: seoKeywords ? seoKeywords.split(',').map(k => k.trim()) : [],
        reference_docs: referenceDocs ? [referenceDocs] : []
      };

      const res = await fetch(`${API_BASE}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const result = await res.json();
        setIsGenerating(false);
        setFormMessage({ type: 'success', text: `Job finished successfully: ID ${result.job_id}` });
        
        // Clear inputs on success
        setTopic('');
        setSeoKeywords('');
        setReferenceDocs('');
        
        // Fetch jobs immediately to show updated table
        fetchJobs();
      } else {
        const errorData = await res.json();
        setIsGenerating(false);
        setFormMessage({ type: 'error', text: `Generation failed: ${errorData.detail || 'Server error'}` });
      }
    } catch (err) {
      setIsGenerating(false);
      setFormMessage({ type: 'error', text: `Network connection failed: ${err.message}` });
    }
  };

  // Compute overall stats metrics
  const totalJobs = jobs.length;
  const successfulJobs = jobs.filter(j => j.status === 'success');
  const failedJobs = jobs.filter(j => j.status === 'failed');
  const passingJobs = successfulJobs.filter(j => j.quality_passed === true);
  
  const passRate = totalJobs > 0 ? Math.round((passingJobs.length / totalJobs) * 100) : 0;
  
  const avgSeoScore = successfulJobs.length > 0 
    ? Math.round(successfulJobs.reduce((acc, j) => acc + (j.quality_score || 0), 0) / successfulJobs.length)
    : 0;

  const totalWords = successfulJobs.reduce((acc, j) => acc + j.word_count, 0);

  // Styled log line parser
  const getLogLineClass = (line) => {
    if (line.includes('[SYSTEM]')) return 'console-line system';
    if (line.includes('| ERROR    |')) return 'console-line error';
    if (line.includes('complete') || line.includes('passed') || line.includes('successfully')) return 'console-line success';
    if (line.includes('| DEBUG    |')) return 'console-line debug';
    return 'console-line info';
  };

  // Simple Regex-based Markdown Parser for architecture docs
  const parseMarkdown = (markdown) => {
    if (!markdown) return '';
    let html = markdown;

    // Convert blockquotes
    html = html.replace(/^\>\s*(.*)$/gm, "<blockquote>$1</blockquote>");

    // Parse tables
    const lines = html.split("\n");
    let inTable = false;
    let tableHeader = true;
    let tableRows = [];
    let parsedLines = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith("|") && line.endsWith("|")) {
        if (!inTable) {
          inTable = true;
          tableRows = [];
          tableHeader = true;
        }
        const cols = line.split("|").slice(1, -1).map(c => c.trim());
        
        // Skip table grid divider lines
        if (cols.every(c => c.match(/^:-*-:$/) || c.match(/^-+$/) || c === "")) {
          tableHeader = false;
          continue;
        }

        if (tableHeader) {
          tableRows.push(`<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`);
          tableHeader = false;
        } else {
          tableRows.push(`<tr>${cols.map(c => `<td>${c}</td>`).join("")}</tr>`);
        }
      } else {
        if (inTable) {
          parsedLines.push(`<div class="table-container"><table><tbody>${tableRows.join("")}</tbody></table></div>`);
          inTable = false;
        }
        parsedLines.push(lines[i]);
      }
    }
    if (inTable) {
      parsedLines.push(`<div class="table-container"><table><tbody>${tableRows.join("")}</tbody></table></div>`);
    }
    html = parsedLines.join("\n");

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Text formatting
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    html = html.replace(/^\-\s*(.*)$/gm, "<li>$1</li>");
    html = html.replace(/\n/g, "<br />");

    return html;
  };

  return (
    <div className="app-container">
      {/* ──────────────── Sidebar Navigation ──────────────── */}
      <aside className="sidebar">
        <div className="logo-section">
          <div className="logo-icon">🚀</div>
          <div className="logo-text">ContentAI Studio</div>
        </div>

        <ul className="nav-menu">
          <li className="nav-item">
            <button 
              className={`nav-btn ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              <span className="nav-btn-icon">📊</span> Overview Stats
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-btn ${activeTab === 'write' ? 'active' : ''}`}
              onClick={() => setActiveTab('write')}
            >
              <span className="nav-btn-icon">✏️</span> Write Article
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-btn ${activeTab === 'logs' ? 'active' : ''}`}
              onClick={() => setActiveTab('logs')}
            >
              <span className="nav-btn-icon">💻</span> Live Terminal
            </button>
          </li>
          <li className="nav-item">
            <button 
              className={`nav-btn ${activeTab === 'docs' ? 'active' : ''}`}
              onClick={() => setActiveTab('docs')}
            >
              <span className="nav-btn-icon">📚</span> Technical Docs
            </button>
          </li>
        </ul>

        <div className="sidebar-footer">
          <div className="api-status">
            <span className={`status-dot ${apiOnline ? 'online' : 'offline'}`}></span>
            API Server: {apiOnline ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>
      </aside>

      {/* ──────────────── Workspace Area ──────────────── */}
      <main className="workspace">
        <header className="header-bar">
          <div>
            <h1 className="page-title">
              {activeTab === 'overview' && 'Production Dashboard'}
              {activeTab === 'write' && 'New Content Brief'}
              {activeTab === 'logs' && 'Real-Time Agent Activity'}
              {activeTab === 'docs' && 'Technical Documentation'}
            </h1>
            <p className="page-subtitle">
              {activeTab === 'overview' && 'Monitor all automated content tasks, quality gates, and KPIs.'}
              {activeTab === 'write' && 'Assign a content research and writing crew to generate articles.'}
              {activeTab === 'logs' && 'Watch CrewAI agents collaborate and output tools logs live.'}
              {activeTab === 'docs' && 'Introspected FastAPI router, agent utility tools, and quality gates.'}
            </p>
          </div>
        </header>

        {/* ── TAB 1: OVERVIEW ── */}
        {activeTab === 'overview' && (
          <>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Jobs</div>
                <div className="stat-value accent-text">{totalJobs}</div>
                <div className="stat-desc">{failedJobs.length} failed jobs</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Quality Pass Rate</div>
                <div className="stat-value primary-text">{passRate}%</div>
                <div className="stat-desc">{passingJobs.length} passed quality gate</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Quality Score</div>
                <div className="stat-value">{avgSeoScore} <span style={{fontSize: '1rem', color: 'var(--text-muted)'}}>/100</span></div>
                <div className="stat-desc">SEO & grammar score aggregate</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Words</div>
                <div className="stat-value accent-text">{totalWords.toLocaleString()}</div>
                <div className="stat-desc">Words written by Writer Agent</div>
              </div>
            </div>

            <div className="glass-panel">
              <div className="panel-header">
                <h2 className="panel-title">Production Status</h2>
                <button className="btn btn-secondary btn-sm" onClick={fetchJobs}>Refresh</button>
              </div>

              <div className="table-container">
                {jobs.length === 0 ? (
                  <p style={{textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)'}}>No jobs recorded yet. Go to "Write Article" to initiate one.</p>
                ) : (
                  <table>
                    <thead>
                      <tr>
                        <th>Job ID</th>
                        <th>Topic</th>
                        <th>Status</th>
                        <th>Score</th>
                        <th>Words</th>
                        <th>Quality Gate</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobs.map((job) => (
                        <tr key={job.job_id}>
                          <td style={{fontFamily: 'var(--font-mono)', fontSize: '0.8rem'}}>{job.job_id}</td>
                          <td style={{fontWeight: 600, maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{job.brief?.topic || job.topic}</td>
                          <td>
                            <span className={`badge ${job.status}`}>
                              {job.status === 'running' && <span className="pulsing-dot"></span>}
                              {job.status}
                            </span>
                          </td>
                          <td>{job.status === 'success' ? `${Math.round(job.quality_score || 0)}/100` : '—'}</td>
                          <td>{job.status === 'success' ? job.word_count : '—'}</td>
                          <td>
                            {job.status === 'success' ? (
                              job.quality_passed ? (
                                <span className="badge-passed">PASS</span>
                              ) : (
                                <span className="badge-failed">FAIL</span>
                              )
                            ) : '—'}
                          </td>
                          <td>
                            <button 
                              className="btn btn-secondary btn-sm"
                              onClick={() => setSelectedJob(job)}
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </>
        )}

        {/* ── TAB 2: WRITE ARTICLE ── */}
        {activeTab === 'write' && (
          <div className="form-grid">
            <div className="glass-panel">
              <h2 style={{borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.75rem', marginBottom: '1.5rem'}}>Content Brief Creator</h2>
              
              <form onSubmit={handleSubmitBrief} style={{display: 'flex', flexDirection: 'column', gap: '1.25rem'}}>
                <div className="form-group">
                  <label htmlFor="topic">Topic *</label>
                  <input 
                    type="text" 
                    id="topic" 
                    placeholder="Enter article topic..." 
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    required
                    disabled={isGenerating}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="tone">Writing Tone</label>
                  <select 
                    id="tone" 
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    disabled={isGenerating}
                  >
                    <option value="professional">Professional</option>
                    <option value="casual">Casual</option>
                    <option value="academic">Academic</option>
                    <option value="persuasive">Persuasive</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="wordCount">Target Word Count</label>
                  <div className="range-slider-container">
                    <input 
                      type="range" 
                      id="wordCount" 
                      min="200" 
                      max="3000" 
                      step="100"
                      value={wordCount}
                      onChange={(e) => setWordCount(e.target.value)}
                      disabled={isGenerating}
                    />
                    <span className="range-value">{wordCount} words</span>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="audience">Audience</label>
                  <input 
                    type="text" 
                    id="audience" 
                    value={audience}
                    onChange={(e) => setAudience(e.target.value)}
                    disabled={isGenerating}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="seoKeywords">SEO Keywords (comma separated)</label>
                  <input 
                    type="text" 
                    id="seoKeywords" 
                    placeholder="e.g. artificial intelligence, medical tools" 
                    value={seoKeywords}
                    onChange={(e) => setSeoKeywords(e.target.value)}
                    disabled={isGenerating}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="referenceDocs">Reference Documents (Plagiarism Check Source)</label>
                  <textarea 
                    id="referenceDocs" 
                    rows="3" 
                    placeholder="Paste reference materials to verify against duplication..." 
                    value={referenceDocs}
                    onChange={(e) => setReferenceDocs(e.target.value)}
                    disabled={isGenerating}
                  />
                </div>

                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={isGenerating}
                  style={{marginTop: '1rem', justifySelf: 'start'}}
                >
                  {isGenerating ? 'Running Crew...' : 'Generate Content'}
                </button>

                {formMessage.text && (
                  <div className={`badge ${formMessage.type === 'error' ? 'failed' : formMessage.type === 'success' ? 'success' : 'running'}`} style={{width: '100%', justifyContent: 'center', padding: '0.75rem'}}>
                    {formMessage.text}
                  </div>
                )}
              </form>
            </div>

            <div className="glass-panel">
              <h2 style={{borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.75rem', marginBottom: '1.5rem'}}>Recent Submissions</h2>
              
              <div className="table-container">
                {jobs.slice(0, 5).map((job) => (
                  <div key={job.job_id} style={{padding: '1rem 0', borderBottom: '1px solid rgba(255,255,255,0.03)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                    <div style={{maxWidth: '70%'}}>
                      <div style={{fontWeight: 'bold', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>{job.brief?.topic || job.topic}</div>
                      <div style={{fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)'}}>{job.job_id} | Tone: {job.brief?.tone}</div>
                    </div>
                    <span className={`badge ${job.status}`}>
                      {job.status === 'running' && <span className="pulsing-dot"></span>}
                      {job.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 3: LIVE TERMINAL LOGS ── */}
        {activeTab === 'logs' && (
          <div className="glass-panel">
            <div className="panel-header">
              <h2 className="panel-title">Console Activity Feed</h2>
              <span className="api-status" style={{background: 'rgba(0,245,212,0.1)', color: 'var(--accent)', border: '1px solid rgba(0,245,212,0.2)'}}>
                <span className="status-dot online" style={{color: 'var(--accent)'}}></span> Live Stream Active
              </span>
            </div>

            <div className="console-box">
              {logs.length === 0 ? (
                <div className="console-line system">Waiting for agent logging events...</div>
              ) : (
                logs.map((line, idx) => (
                  <div key={idx} className={getLogLineClass(line)}>{line}</div>
                ))
              )}
              <div ref={consoleEndRef} />
            </div>

            <div className="console-actions">
              <div className="console-options">
                <label style={{display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer'}}>
                  <input 
                    type="checkbox" 
                    checked={autoscroll}
                    onChange={(e) => setAutoscroll(e.target.checked)}
                  />
                  Auto-scroll to bottom
                </label>
              </div>

              <button className="btn btn-secondary btn-sm" onClick={() => setLogs([])}>Clear Console</button>
            </div>
          </div>
        )}

        {/* ── TAB 4: API & TECHNICAL DOCS ── */}
        {activeTab === 'docs' && (
          <div className="glass-panel">
            <div className="panel-header">
              <h2 className="panel-title">Project Technical Documentation</h2>
              <div style={{display: 'flex', gap: '0.75rem'}}>
                <button className="btn btn-secondary btn-sm" onClick={fetchDocs}>Reload</button>
                <button className="btn btn-primary btn-sm" onClick={handleRegenerateDocs}>Regenerate Docs</button>
              </div>
            </div>

            <div 
              className="doc-markdown-render"
              dangerouslySetInnerHTML={{ __html: parseMarkdown(docsContent) }}
            />
          </div>
        )}
      </main>

      {/* ──────────────── Inspect Modal Overlay ──────────────── */}
      {selectedJob && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2 className="modal-title">Job Inspection Panel</h2>
              <button className="close-btn" onClick={() => setSelectedJob(null)}>&times;</button>
            </div>
            
            <div className="modal-body">
              <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'}}>
                <div>
                  <h3 style={{fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.25rem'}}>Job Identifier</h3>
                  <code style={{fontFamily: 'var(--font-mono)', padding: '4px 8px', background: 'rgba(0,0,0,0.3)', borderRadius: '4px'}}>{selectedJob.job_id}</code>
                </div>
                <div>
                  <h3 style={{fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.25rem'}}>Created At</h3>
                  <span style={{fontSize: '0.9rem'}}>{new Date(selectedJob.created_at).toLocaleString()}</span>
                </div>
              </div>

              <div>
                <h3 style={{fontSize: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem'}}>Brief Details</h3>
                <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginTop: '0.5rem'}}>
                  <div>
                    <label style={{fontSize: '0.75rem'}}>Topic</label>
                    <div style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{selectedJob.brief?.topic || selectedJob.topic}</div>
                  </div>
                  <div>
                    <label style={{fontSize: '0.75rem'}}>Tone</label>
                    <div style={{fontWeight: 'bold', fontSize: '0.85rem', textTransform: 'capitalize'}}>{selectedJob.brief?.tone || '—'}</div>
                  </div>
                  <div>
                    <label style={{fontSize: '0.75rem'}}>Audience</label>
                    <div style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{selectedJob.brief?.audience || '—'}</div>
                  </div>
                  <div>
                    <label style={{fontSize: '0.75rem'}}>Target Word Count</label>
                    <div style={{fontWeight: 'bold', fontSize: '0.85rem'}}>{selectedJob.brief?.word_count || '—'}</div>
                  </div>
                </div>
              </div>

              {selectedJob.status === 'success' && (
                <>
                  <div>
                    <h3 style={{fontSize: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1rem'}}>Quality Gate Metrics</h3>
                    <div className="metrics-summary-grid">
                      {/* SEO Score */}
                      <div className="metric-bar-group">
                        <div className="metric-bar-label">
                          <span>SEO Score</span>
                          <span>{selectedJob.quality_score ? Math.round(selectedJob.quality_score) : 0}/100</span>
                        </div>
                        <div className="metric-bar-bg">
                          <div 
                            className={`metric-bar-fill ${selectedJob.quality_score >= 70 ? 'success' : 'failed'}`} 
                            style={{width: `${selectedJob.quality_score || 0}%`}}
                          />
                        </div>
                        <div style={{fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem'}}>Threshold: 70 min</div>
                      </div>

                      {/* Quality Gate Status */}
                      <div className="metric-bar-group" style={{display: 'flex', flexDirection: 'column', justifycontent: 'center'}}>
                        <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontWeight: 600}}>Gate Result</div>
                        <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                          <span className={`badge ${selectedJob.quality_passed ? 'success' : 'failed'}`}>
                            {selectedJob.quality_passed ? 'PASSED' : 'FAILED'}
                          </span>
                        </div>
                        <div style={{fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem'}}>Auto-Evaluated</div>
                      </div>

                      {/* Word Count */}
                      <div className="metric-bar-group">
                        <div style={{fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.25rem', fontWeight: 600}}>Article Length</div>
                        <div style={{fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--accent)'}}>{selectedJob.word_count} words</div>
                        <div style={{fontSize: '0.7rem', color: 'var(--text-secondary)', marginTop: '0.25rem'}}>Target: {selectedJob.brief?.word_count}</div>
                      </div>
                    </div>

                    {selectedJob.quality_reasons && selectedJob.quality_reasons.length > 0 && (
                      <div style={{marginTop: '1rem', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '1rem', borderRadius: '8px'}}>
                        <h4 style={{color: 'var(--error)', fontSize: '0.85rem', marginBottom: '0.5rem'}}>Gate Verification Failures / Warnings:</h4>
                        <ul style={{margin: 0, paddingLeft: '1.25rem', fontSize: '0.8rem', color: '#fca5a5'}}>
                          {selectedJob.quality_reasons.map((r, i) => <li key={i}>{r}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>

                  <div>
                    <h3 style={{fontSize: '1rem', borderBottom: '1px solid var(--border-glass)', paddingBottom: '0.5rem', marginBottom: '1rem'}}>Generated Article Output</h3>
                    <div className="article-text">{selectedJob.article}</div>
                  </div>
                </>
              )}

              {selectedJob.status === 'failed' && (
                <div style={{background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '1.5rem', borderRadius: '12px'}}>
                  <h3 style={{color: 'var(--error)', fontSize: '1rem', marginTop: 0}}>Execution Failed</h3>
                  <p style={{color: '#fca5a5', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', whiteSpace: 'pre-wrap'}}>{selectedJob.error}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
