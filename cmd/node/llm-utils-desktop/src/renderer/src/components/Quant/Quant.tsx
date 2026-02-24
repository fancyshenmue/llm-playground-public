
import { useState } from 'react'
import { Play, FileCode, BarChart3, Shield, Info, Loader2, Copy, Check } from 'lucide-react'
import './Quant.less'

interface QuantProps {
    llmConfig: {
        provider: string
        model: string
        baseUrl?: string
    }
}

interface QuantOptions {
    strategyName: string
    description: string
    indicators: string[]
    riskManagement: string
    outputFile: string
}

const Quant: React.FC<QuantProps> = ({ llmConfig }) => {
    const [isGenerating, setIsGenerating] = useState(false)
    const [generatedCode, setGeneratedCode] = useState<string | null>(null)
    const [copying, setCopying] = useState(false)
    const [options, setOptions] = useState<QuantOptions>({
        strategyName: 'New Strategy',
        description: 'A trend following strategy using EMA crossover.',
        indicators: ['EMA 20', 'EMA 50', 'RSI'],
        riskManagement: 'Stop loss at 2 ATR, Take profit at 4 ATR.',
        outputFile: 'output/trade_strategy/new_strategy.pine'
    })

    const handleIndicatorChange = (index: number, value: string) => {
        const newIndicators = [...options.indicators]
        newIndicators[index] = value
        setOptions({ ...options, indicators: newIndicators })
    }

    const addIndicator = () => {
        setOptions({ ...options, indicators: [...options.indicators, ''] })
    }

    const removeIndicator = (index: number) => {
        const newIndicators = options.indicators.filter((_, i) => i !== index)
        setOptions({ ...options, indicators: newIndicators })
    }

    const handleGenerate = async () => {
        if (isGenerating) return
        setIsGenerating(true)
        setGeneratedCode(null)

        try {
            const result = await window.api?.generateQuantStrategy(options, llmConfig)
            if (result?.code) {
                setGeneratedCode(result.code)
            }
        } catch (error: any) {
            console.error('Generation failed:', error)
            alert(`Error: ${error.message}`)
        } finally {
            setIsGenerating(false)
        }
    }

    const handleCopy = () => {
        if (!generatedCode) return
        navigator.clipboard.writeText(generatedCode)
        setCopying(true)
        setTimeout(() => setCopying(false), 2000)
    }

    return (
        <div className="quant-container">
            <div className="quant-grid">
                <div className="quant-form">
                    <header>
                        <BarChart3 size={18} />
                        <span>Strategy Configuration</span>
                    </header>

                    <div className="form-content">
                        <div className="form-group">
                            <label>Strategy Name</label>
                            <input
                                type="text"
                                value={options.strategyName}
                                onChange={(e) => setOptions({ ...options, strategyName: e.target.value })}
                            />
                        </div>

                        <div className="form-group">
                            <label>Description & Logic</label>
                            <textarea
                                value={options.description}
                                onChange={(e) => setOptions({ ...options, description: e.target.value })}
                                placeholder="Describe your strategy entry/exit conditions..."
                                rows={4}
                            />
                        </div>

                        <div className="form-group">
                            <label>Indicators</label>
                            <div className="indicators-list">
                                {options.indicators.map((indicator, index) => (
                                    <div key={index} className="indicator-row">
                                        <input
                                            type="text"
                                            value={indicator}
                                            onChange={(e) => handleIndicatorChange(index, e.target.value)}
                                        />
                                        <button onClick={() => removeIndicator(index)} className="remove-btn">×</button>
                                    </div>
                                ))}
                                <button onClick={addIndicator} className="add-btn">+ Add Indicator</button>
                            </div>
                        </div>

                        <div className="form-group">
                            <label><Shield size={12} /> Risk Management</label>
                            <textarea
                                value={options.riskManagement}
                                onChange={(e) => setOptions({ ...options, riskManagement: e.target.value })}
                                placeholder="Describe SL, TP, trailing stops..."
                                rows={3}
                            />
                        </div>

                        <div className="form-group">
                            <label>Output File</label>
                            <input
                                type="text"
                                value={options.outputFile}
                                onChange={(e) => setOptions({ ...options, outputFile: e.target.value })}
                            />
                        </div>

                        <div className="actions">
                            <button
                                className={`generate-btn ${isGenerating ? 'loading' : ''}`}
                                onClick={handleGenerate}
                                disabled={isGenerating}
                            >
                                {isGenerating ? <Loader2 className="spinning" size={16} /> : <Play size={16} />}
                                <span>{isGenerating ? 'Generating...' : 'Generate Pine Script'}</span>
                            </button>
                        </div>
                    </div>
                </div>

                <div className="quant-preview">
                    <header>
                        <FileCode size={18} />
                        <span>Pine Script Preview</span>
                        <div className="header-actions">
                            {generatedCode && (
                                <button onClick={handleCopy} className="icon-btn">
                                    {copying ? <Check size={14} color="#4caf50" /> : <Copy size={14} />}
                                </button>
                            )}
                        </div>
                    </header>

                    <div className="preview-content">
                        {isGenerating ? (
                            <div className="preview-loading">
                                <Loader2 className="spinning" size={32} />
                                <span>Architecting your strategy...</span>
                            </div>
                        ) : generatedCode ? (
                            <pre><code>{generatedCode}</code></pre>
                        ) : (
                            <div className="preview-placeholder">
                                <Info size={32} />
                                <span>Configure your strategy and click Generate</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Quant
