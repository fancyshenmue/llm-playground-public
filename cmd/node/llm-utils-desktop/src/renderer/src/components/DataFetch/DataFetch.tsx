import { useState } from 'react'
import { Database, Calendar, FolderOpen, Loader2 } from 'lucide-react'
import './DataFetch.less'

interface DataFetchState {
    symbol: string
    timeframes: string[]
    startDate: string
    endDate: string
    outputDir: string
    limit: number
}

interface FetchProgressState {
    isProcessing: boolean
    current: number
    total: number
    currentTimeframe: string
    status: string
}

const AVAILABLE_TIMEFRAMES = [
    { value: '1m', label: '1 Minute' },
    { value: '5m', label: '5 Minutes' },
    { value: '15m', label: '15 Minutes' },
    { value: '30m', label: '30 Minutes' },
    { value: '1h', label: '1 Hour' },
    { value: '4h', label: '4 Hours' },
    { value: '1d', label: '1 Day' },
    { value: '1w', label: '1 Week' },
    { value: '1M', label: '1 Month' },
    { value: '1y', label: '1 Year' }
]

const DataFetch: React.FC = () => {
    const [options, setOptions] = useState<DataFetchState>({
        symbol: 'BTCUSDT',
        timeframes: ['1h', '4h', '1d', '1w'],
        startDate: '2024-01-01',
        endDate: '',
        outputDir: 'dataset/trading',
        limit: 1000
    })

    const [progress, setProgress] = useState<FetchProgressState>({
        isProcessing: false,
        current: 0,
        total: 0,
        currentTimeframe: '',
        status: ''
    })

    const [result, setResult] = useState<{ filesCreated: string[]; totalRecords: number } | null>(null)
    const [error, setError] = useState<string | null>(null)

    const toggleTimeframe = (tf: string) => {
        setOptions(prev => ({
            ...prev,
            timeframes: prev.timeframes.includes(tf)
                ? prev.timeframes.filter(t => t !== tf)
                : [...prev.timeframes, tf]
        }))
    }

    const handleSelectOutputDir = async () => {
        try {
            const paths = await window.api.selectFiles({
                properties: ['openDirectory']
            })
            if (paths && paths.length > 0) {
                setOptions(prev => ({ ...prev, outputDir: paths[0] }))
            }
        } catch (err) {
            console.error('Directory selection failed', err)
        }
    }

    const handleFetch = async () => {
        // Validation
        if (!options.symbol.trim()) {
            setError('Please enter a symbol')
            return
        }
        if (options.timeframes.length === 0) {
            setError('Please select at least one timeframe')
            return
        }

        setError(null)
        setResult(null)
        setProgress({
            isProcessing: true,
            current: 0,
            total: options.timeframes.length,
            currentTimeframe: '',
            status: 'Starting...'
        })

        try {
            // Setup progress listener
            window.api.onFetchProgress((progressData) => {
                setProgress(prev => ({
                    ...prev,
                    current: progressData.current,
                    total: progressData.total,
                    currentTimeframe: progressData.timeframe,
                    status: progressData.status
                }))
            })

            const fetchResult = await window.api.fetchTradingData({
                symbol: options.symbol,
                timeframes: options.timeframes,
                startDate: options.startDate,
                endDate: options.endDate || undefined,
                outputDir: options.outputDir,
                limit: options.limit
            })

            if (fetchResult.success) {
                setResult({
                    filesCreated: fetchResult.filesCreated,
                    totalRecords: fetchResult.totalRecords
                })
            } else {
                setError(fetchResult.error || 'Unknown error occurred')
            }
        } catch (err: any) {
            setError(err.message || 'Failed to fetch trading data')
        } finally {
            setProgress(prev => ({ ...prev, isProcessing: false }))
        }
    }

    const progressPercent = progress.total > 0
        ? Math.round((progress.current / progress.total) * 100)
        : 0

    return (
        <div className="data-fetch-container">
            <div className="fetch-grid">
                <div className="fetch-form">
                    <header>
                        <Database size={16} />
                        Data Fetch Configuration
                    </header>

                    <div className="form-content">
                        <div className="form-group">
                            <label>Trading Symbol</label>
                            <input
                                type="text"
                                value={options.symbol}
                                onChange={(e) => setOptions({ ...options, symbol: e.target.value.toUpperCase() })}
                                placeholder="BTCUSDT"
                            />
                        </div>

                        <div className="form-group">
                            <label>Timeframes</label>
                            <div className="timeframe-grid">
                                {AVAILABLE_TIMEFRAMES.map(tf => (
                                    <label key={tf.value} className="checkbox-item">
                                        <input
                                            type="checkbox"
                                            checked={options.timeframes.includes(tf.value)}
                                            onChange={() => toggleTimeframe(tf.value)}
                                        />
                                        <span>{tf.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="form-group">
                            <label>
                                <Calendar size={14} />
                                Start Date
                            </label>
                            <input
                                type="date"
                                value={options.startDate}
                                onChange={(e) => setOptions({ ...options, startDate: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label>
                                <Calendar size={14} />
                                End Date (Optional)
                            </label>
                            <input
                                type="date"
                                value={options.endDate}
                                onChange={(e) => setOptions({ ...options, endDate: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label>
                                <FolderOpen size={14} />
                                Output Directory
                            </label>
                            <div className="input-with-button">
                                <input
                                    type="text"
                                    value={options.outputDir}
                                    onChange={(e) => setOptions({ ...options, outputDir: e.target.value })}
                                    placeholder="dataset/trading"
                                />
                                <button onClick={handleSelectOutputDir} className="browse-btn">
                                    Browse
                                </button>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Candle Limit</label>
                            <input
                                type="number"
                                value={options.limit}
                                onChange={(e) => setOptions({ ...options, limit: parseInt(e.target.value) || 1000 })}
                                min="1"
                                max="10000"
                            />
                            <span className="hint">Maximum candles per timeframe (ignored if using date range)</span>
                        </div>

                        {error && (
                            <div className="error-message">
                                {error}
                            </div>
                        )}

                        <div className="actions">
                            <button
                                className={`fetch-btn ${progress.isProcessing ? 'loading' : ''}`}
                                onClick={handleFetch}
                                disabled={progress.isProcessing}
                            >
                                {progress.isProcessing ? (
                                    <>
                                        <Loader2 size={16} className="spinning" />
                                        Fetching...
                                    </>
                                ) : (
                                    <>
                                        <Database size={16} />
                                        Fetch Data
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>

                <div className="fetch-preview">
                    <header>
                        Status & Results
                    </header>

                    <div className="preview-content">
                        {progress.isProcessing && (
                            <div className="progress-section">
                                <h3>Downloading...</h3>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${progressPercent}%` }}
                                    />
                                </div>
                                <div className="progress-text">
                                    {progressPercent}% ({progress.current}/{progress.total} timeframes)
                                </div>
                                {progress.currentTimeframe && (
                                    <div className="current-task">
                                        Current: {options.symbol}_{progress.currentTimeframe}.csv
                                    </div>
                                )}
                                <div className="status-text">{progress.status}</div>
                            </div>
                        )}

                        {!progress.isProcessing && !result && (
                            <div className="preview-placeholder">
                                <Database size={48} />
                                <span>Configure settings and click "Fetch Data" to begin</span>
                            </div>
                        )}

                        {!progress.isProcessing && result && (
                            <div className="result-section">
                                <h3>✅ Download Complete!</h3>
                                <div className="result-summary">
                                    <div className="summary-item">
                                        <strong>Files Created:</strong>
                                        <span>{result.filesCreated.length}</span>
                                    </div>
                                    <div className="summary-item">
                                        <strong>Total Records:</strong>
                                        <span>{result.totalRecords.toLocaleString()}</span>
                                    </div>
                                </div>
                                <div className="file-list">
                                    <h4>Generated Files:</h4>
                                    {result.filesCreated.map((file, idx) => (
                                        <div key={idx} className="file-item">
                                            📄 {file}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default DataFetch
