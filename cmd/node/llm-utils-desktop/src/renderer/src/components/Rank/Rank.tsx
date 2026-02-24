import { useState, useEffect, useRef } from 'react'
import {
    Play,
    StopCircle,
    Folder,
    Copy,
    Check,
    ChevronDown,
    FileText,
    Table
} from 'lucide-react'
import './Rank.less'

// Rank component for image evaluation using vision models

interface RankProgress {
    current: number
    total: number
    status: string
    currentImage?: string
}

interface RankResult {
    filename: string
    score: number
    reason: string
    imagePath: string
}

interface RankProps {
    llmConfig: {
        provider: string
        model: string
        baseUrl?: string
    }
    selection?: { path: string; timestamp: number; isDirectory: boolean } | null
}

const Rank = ({ llmConfig, selection }: RankProps) => {
    const [options, setOptions] = useState({
        dir: '',
        model: 'llama3.2-vision',
        outputDir: '',
        outputFilename: 'ranking_results.md',
        format: 'md' as 'md' | 'html',
        prompt: "Please rate this image from 1 to 10 based on visual appeal and style consistency. Return only the number and a short reason."
    })

    const [isRanking, setIsRanking] = useState(false)
    const [progress, setProgress] = useState<RankProgress | null>(null)
    const [logs, setLogs] = useState<string[]>([])
    const [results, setResults] = useState<RankResult[]>([])
    const [copied, setCopied] = useState(false)
    const [availableModels, setAvailableModels] = useState<string[]>([])

    // Pagination state
    const [currentPage, setCurrentPage] = useState(1)
    const itemsPerPage = 10

    const logsEndRef = useRef<HTMLDivElement>(null)

    // Scroll to bottom of logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    // Load available models and check if already running
    useEffect(() => {
        const init = async () => {
            if (window.api?.listModels) {
                const models = await window.api.listModels('ollama', llmConfig.baseUrl)
                setAvailableModels(models)
            }
            if (window.api?.isRankRunning) {
                const running = await window.api.isRankRunning()
                setIsRanking(running)
            }
        }
        init()
    }, [llmConfig.baseUrl])

    // Listen for progress updates
    useEffect(() => {
        if (window.api?.onRankProgress) {
            return window.api.onRankProgress((p) => {
                setProgress(p)
                setLogs((prev) => [...prev, `${p.status}`])
            })
        }
        return undefined
    }, [])

    // Handle selection from sidebar explorer
    useEffect(() => {
        if (selection && selection.isDirectory) {
            setOptions(prev => ({ ...prev, dir: selection.path }))
        }
    }, [selection])

    // Auto-update filename extension when format changes
    useEffect(() => {
        const currentFilename = options.outputFilename
        const baseName = currentFilename.replace(/\.(md|html)$/i, '')
        const newExtension = options.format === 'md' ? '.md' : '.html'
        const newFilename = baseName + newExtension

        if (newFilename !== currentFilename) {
            setOptions(prev => ({ ...prev, outputFilename: newFilename }))
        }
    }, [options.format])

    const handleBrowse = async () => {
        const paths = await window.api?.selectFiles({ properties: ['openDirectory'] })
        if (paths && paths.length > 0) {
            setOptions({ ...options, dir: paths[0] })
        }
    }

    const handleBrowseOutput = async () => {
        const paths = await window.api?.selectFiles({ properties: ['openDirectory'] })
        if (paths && paths.length > 0) {
            setOptions({ ...options, outputDir: paths[0] })
        }
    }

    const handleStart = async () => {
        if (isRanking) return
        if (!options.dir) {
            setLogs(['ERROR: Please select a directory first.'])
            return
        }

        // Reset state for new ranking
        setIsRanking(true)
        setLogs([]) // Clear previous logs
        setResults([]) // Clear previous results
        setProgress({ current: 0, total: 0, status: 'Initializing...' })

        // Brief delay to ensure state is cleared
        await new Promise(resolve => setTimeout(resolve, 100))

        setLogs(['Starting Image Ranking Workflow...'])

        try {
            // Ensure we use the selected LLM config for host/port but allow overriding the model
            const activeConfig = { ...llmConfig, model: options.model }

            // Map output filename to absolute path
            const finalOutputDir = options.outputDir || options.dir
            const finalOutputFile = `${finalOutputDir}/${options.outputFilename}`

            const result = await window.api?.startRank({ ...options, outputFile: finalOutputFile }, activeConfig)
            if (result?.success) {
                setResults(result.results || [])
                setCurrentPage(1) // Reset to first page when new results arrive
                setLogs((prev) => [...prev, '--- RANKING COMPLETE ---'])
            } else if (result?.error) {
                setLogs((prev) => [...prev, `ERROR: ${result.error}`])
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `ERROR: ${error.message}`])
        } finally {
            setIsRanking(false)
        }
    }

    const handleCancel = async () => {
        await window.api?.cancelRank()
        setLogs((prev) => [...prev, 'Cancellation requested...'])
    }

    const handleCopyResults = () => {
        if (results.length === 0) return
        const header = `| Rank | Image | Score | Reason |\n| :--- | :--- | :--- | :--- |\n`
        const rows = results.map((r, i) => `| ${i + 1} | ${r.filename} | **${r.score}** | ${r.reason} |`).join('\n')
        navigator.clipboard.writeText(header + rows)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    // Calculate pagination
    const totalPages = Math.ceil(results.length / itemsPerPage)
    const startIndex = (currentPage - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    const currentResults = results.slice(startIndex, endIndex)

    const handlePrevPage = () => {
        if (currentPage > 1) setCurrentPage(currentPage - 1)
    }

    const handleNextPage = () => {
        if (currentPage < totalPages) setCurrentPage(currentPage + 1)
    }

    return (
        <div className="rank-container">
            <div className="rank-grid">
                {/* Left: Configuration */}
                <div className="rank-form">
                    <header>
                        <Table size={18} />
                        <span>Ranking Configuration</span>
                    </header>
                    <div className="form-content">
                        <div className="form-group">
                            <label>Target Directory</label>
                            <div className="file-selector">
                                <input
                                    type="text"
                                    value={options.dir}
                                    onChange={(e) => setOptions({ ...options, dir: e.target.value })}
                                    placeholder="Select directory with images..."
                                />
                                <button type="button" onClick={handleBrowse} title="Browse Directory">
                                    <Folder size={14} />
                                </button>
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Vision Model</label>
                                <div className="select-wrapper">
                                    <select
                                        value={options.model}
                                        onChange={(e) => setOptions({ ...options, model: e.target.value })}
                                    >
                                        {availableModels.filter(m => m.includes('vision')).map(model => (
                                            <option key={model} value={model}>{model}</option>
                                        ))}
                                        {!availableModels.some(m => m.includes('vision')) && (
                                            <option value="llama3.2-vision">llama3.2-vision (default)</option>
                                        )}
                                    </select>
                                    <ChevronDown size={14} className="select-icon" />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Export Format</label>
                                <div className="select-wrapper">
                                    <select
                                        value={options.format}
                                        onChange={(e) => setOptions({ ...options, format: e.target.value as 'md' | 'html' })}
                                    >
                                        <option value="md">Markdown (.md)</option>
                                        <option value="html">HTML (.html)</option>
                                    </select>
                                    <ChevronDown size={14} className="select-icon" />
                                </div>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Output Directory</label>
                            <div className="file-selector">
                                <input
                                    type="text"
                                    value={options.outputDir}
                                    onChange={(e) => setOptions({ ...options, outputDir: e.target.value })}
                                    placeholder="Same as target dir if empty..."
                                />
                                <button type="button" onClick={handleBrowseOutput} title="Browse Output Directory">
                                    <Folder size={14} />
                                </button>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Output Filename</label>
                            <input
                                type="text"
                                value={options.outputFilename}
                                onChange={(e) => setOptions({ ...options, outputFilename: e.target.value })}
                                placeholder="e.g. results.md"
                            />
                        </div>

                        <div className="form-group">
                            <label>Evaluation Prompt</label>
                            <textarea
                                rows={3}
                                value={options.prompt}
                                onChange={(e) => setOptions({ ...options, prompt: e.target.value })}
                                placeholder="Enter evaluation criteria..."
                            />
                        </div>

                        <div className="actions">
                            {!isRanking ? (
                                <button className="primary-btn" onClick={handleStart}>
                                    <Play size={16} />
                                    Start Ranking
                                </button>
                            ) : (
                                <button className="danger-btn" onClick={handleCancel}>
                                    <StopCircle size={16} />
                                    Cancel
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right: Logs & Results */}
                <div className="rank-monitor">
                    <header>
                        <FileText size={18} />
                        <span>Progress & Results</span>
                    </header>
                    <div className="monitor-content">
                        <div className="terminal">
                            {logs.map((log, i) => (
                                <div key={i} className="log-line">{log}</div>
                            ))}
                            <div ref={logsEndRef} />
                        </div>

                        {progress && (
                            <div className="progress-container">
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${(progress.current / progress.total) * 100}%` }}
                                    />
                                </div>
                                <div className="progress-stats">
                                    <span>{progress.status}</span>
                                    <span>{progress.current} / {progress.total}</span>
                                </div>
                            </div>
                        )}

                        {results.length > 0 && (
                            <div className="results-section">
                                <div className="results-header">
                                    <span>Results ({results.length} total)</span>
                                    <button className="icon-btn" onClick={handleCopyResults} title="Copy as Markdown Table">
                                        {copied ? <Check size={14} color="#4caf50" /> : <Copy size={14} />}
                                    </button>
                                </div>
                                <div className="results-table-container">
                                    <table className="results-table">
                                        <thead>
                                            <tr>
                                                <th>Rank</th>
                                                <th>Image</th>
                                                <th>Score</th>
                                                <th>Reason</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {currentResults.map((r, i) => {
                                                const globalIndex = startIndex + i
                                                return (
                                                    <tr key={i}>
                                                        <td className="rank-col">{globalIndex + 1}</td>
                                                        <td className="file-col">{r.filename}</td>
                                                        <td className="score-col">
                                                            <span className={`score-badge score-${r.score}`}>
                                                                {r.score}
                                                            </span>
                                                        </td>
                                                        <td className="reason-col">{r.reason}</td>
                                                    </tr>
                                                )
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                                {totalPages > 1 && (
                                    <div className="pagination">
                                        <button
                                            className="page-btn"
                                            onClick={handlePrevPage}
                                            disabled={currentPage === 1}
                                        >
                                            ← Prev
                                        </button>
                                        <span className="page-info">
                                            Page {currentPage} of {totalPages}
                                        </span>
                                        <button
                                            className="page-btn"
                                            onClick={handleNextPage}
                                            disabled={currentPage === totalPages}
                                        >
                                            Next →
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Rank
