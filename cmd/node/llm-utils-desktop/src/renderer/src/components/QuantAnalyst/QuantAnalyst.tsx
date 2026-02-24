import { useState, useEffect } from 'react'
import {
    Beaker,
    FileSearch,
    FileText,
    Loader2,
    Copy,
    Check,
    Info,
    X,
    Plus
} from 'lucide-react'
import './QuantAnalyst.less'

interface QuantAnalystProps {
    llmConfig: {
        provider: string
        model: string
        baseUrl?: string
    }
    availableModels: string[]
    isLoadingModels: boolean
}

interface QuantAnalystState {
    inputs: string[]
    logic?: string
    limit: number
    useAnalyst: boolean
    distill: boolean
    promptOnly: boolean
    outputFile: string
    model: string
}

const QuantAnalyst: React.FC<QuantAnalystProps> = ({ llmConfig, availableModels, isLoadingModels }) => {
    const [isProcessing, setIsProcessing] = useState(false)
    const [generatedPrompt, setGeneratedPrompt] = useState<string | null>(null)
    const [analysis, setAnalysis] = useState<string | null>(null)
    const [copying, setCopying] = useState(false)
    const [options, setOptions] = useState<QuantAnalystState>({
        inputs: [],
        logic: '',
        limit: 50,
        useAnalyst: true,
        distill: true,
        promptOnly: true,
        outputFile: 'output/trade_strategy/distilled_prompt.txt',
        model: llmConfig.model
    })

    // Update local model when global config changes or models load
    useEffect(() => {
        if (availableModels.length > 0 && !options.model) {
            setOptions(prev => ({ ...prev, model: availableModels[0] }))
        }
    }, [availableModels])

    const handleSelectFiles = async () => {
        try {
            const paths = await window.api.selectFiles({
                title: 'Select TradingView CSV Data',
                properties: ['openFile', 'multiSelections']
            })
            if (paths && paths.length > 0) {
                setOptions(prev => ({
                    ...prev,
                    inputs: Array.from(new Set([...prev.inputs, ...paths]))
                }))
            }
        } catch (err) {
            console.error('File selection failed', err)
        }
    }

    const removeInput = (index: number) => {
        setOptions(prev => ({
            ...prev,
            inputs: prev.inputs.filter((_, i) => i !== index)
        }))
    }

    const handleRun = async () => {
        if (isProcessing) return
        if (options.inputs.length === 0) {
            alert('Please select at least one input CSV file.')
            return
        }

        setIsProcessing(true)
        setGeneratedPrompt(null)
        setAnalysis(null)

        try {
            const result = await window.api.runQuantAnalyst(
                { ...options, analystModel: options.model },
                llmConfig
            )
            if (result) {
                setGeneratedPrompt(result.prompt)
                if (result.analysis) setAnalysis(result.analysis)
                if (result.filePath) {
                    console.log('Distilled prompt saved to:', result.filePath)
                }
            }
        } catch (error: any) {
            console.error('Analyst workflow failed:', error)
            alert(`Error: ${error.message}`)
        } finally {
            setIsProcessing(false)
        }
    }

    const handleCopy = () => {
        if (!generatedPrompt) return
        navigator.clipboard.writeText(generatedPrompt)
        setCopying(true)
        setTimeout(() => setCopying(false), 2000)
    }

    return (
        <div className="quant-analyst-container">
            <div className="analyst-grid">
                <div className="analyst-form">
                    <header>
                        <Beaker size={18} />
                        <span>Analyst Configuration</span>
                    </header>

                    <div className="form-content">
                        <div className="form-group">
                            <label>Input CSV Files (Multi-Timeframe)</label>
                            <div className="file-list">
                                {options.inputs.length === 0 && (
                                    <div className="empty-files">No files selected</div>
                                )}
                                {options.inputs.map((file, idx) => (
                                    <div key={idx} className="file-item">
                                        <span title={file}>{file.split(/[\\/]/).pop()}</span>
                                        <button onClick={() => removeInput(idx)}><X size={12} /></button>
                                    </div>
                                ))}
                            </div>
                            <button className="add-file-btn" onClick={handleSelectFiles}>
                                <Plus size={14} /> Add Data Records
                            </button>
                        </div>

                        <div className="form-group">
                            <label>Model Selection</label>
                            <div className="select-wrapper">
                                <select
                                    value={options.model}
                                    onChange={(e) => setOptions({ ...options, model: e.target.value })}
                                    disabled={isLoadingModels || availableModels.length === 0}
                                >
                                    {availableModels.map(model => (
                                        <option key={model} value={model}>{model}</option>
                                    ))}
                                    {availableModels.length === 0 && (
                                        <option value="">No models found</option>
                                    )}
                                </select>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Strategy Logic</label>
                            <textarea
                                value={options.logic}
                                onChange={(e) => setOptions({ ...options, logic: e.target.value })}
                                placeholder="Describe strategy entry/exit logic..."
                                rows={3}
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Candle Limit</label>
                                <input
                                    type="number"
                                    value={options.limit}
                                    onChange={(e) => setOptions({ ...options, limit: parseInt(e.target.value) })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Analyst Options</label>
                                <div className="checkbox-group">
                                    <label className="checkbox-item">
                                        <input
                                            type="checkbox"
                                            checked={options.useAnalyst}
                                            onChange={(e) => setOptions({ ...options, useAnalyst: e.target.checked })}
                                        />
                                        <span>Market Analysis</span>
                                    </label>
                                    <label className="checkbox-item">
                                        <input
                                            type="checkbox"
                                            checked={options.distill}
                                            onChange={(e) => setOptions({ ...options, distill: e.target.checked })}
                                        />
                                        <span>Distill Data</span>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <div className="form-group">
                            <label>Output Filename (.txt)</label>
                            <input
                                type="text"
                                value={options.outputFile}
                                onChange={(e) => setOptions({ ...options, outputFile: e.target.value })}
                            />
                        </div>

                        <div className="actions">
                            <button
                                className={`run-btn ${isProcessing ? 'loading' : ''}`}
                                onClick={handleRun}
                                disabled={isProcessing}
                            >
                                {isProcessing ? <Loader2 className="spinning" size={16} /> : <FileSearch size={16} />}
                                <span>{isProcessing ? 'Processing...' : 'Run Analysis & Distill'}</span>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="analyst-preview">
                    <header>
                        <FileText size={18} />
                        <span>Distilled Prompt Preview</span>
                        <div className="header-actions">
                            {generatedPrompt && (
                                <button onClick={handleCopy} className="icon-btn">
                                    {copying ? <Check size={14} color="#4caf50" /> : <Copy size={14} />}
                                </button>
                            )}
                        </div>
                    </header>

                    <div className="preview-content">
                        {isProcessing ? (
                            <div className="preview-loading">
                                <Loader2 className="spinning" size={32} />
                                <span>Distilling market data...</span>
                            </div>
                        ) : generatedPrompt ? (
                            <div className="preview-scroller">
                                {analysis && (
                                    <div className="analysis-box">
                                        <h4>Market Insights</h4>
                                        <p>{analysis}</p>
                                    </div>
                                )}
                                <pre><code>{generatedPrompt}</code></pre>
                            </div>
                        ) : (
                            <div className="preview-placeholder">
                                <Info size={32} />
                                <span>Select data files and run analysis</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default QuantAnalyst
