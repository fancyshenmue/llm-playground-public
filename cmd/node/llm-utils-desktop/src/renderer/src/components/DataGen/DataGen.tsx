import { useState, useEffect, useRef } from 'react'
import { Play, Folder, Database, Layers, Tag, Clock, CheckCircle, AlertCircle, Loader2, Sparkles, FileText, StopCircle, Copy, Check, ChevronDown } from 'lucide-react'
import './DataGen.less'

interface DataGenProps {
    llmConfig: {
        provider: string
        model: string
        baseUrl?: string
    }
    selection?: { path: string; timestamp: number; isDirectory: boolean } | null
    appConfig?: any
}

interface Progress {
    current: number
    total: number
    status: string
    imagePath?: string
}

const DataGen: React.FC<DataGenProps> = ({ llmConfig, selection, appConfig }) => {
    const [isGenerating, setIsGenerating] = useState(false)
    const [copied, setCopied] = useState(false)
    const [progress, setProgress] = useState<Progress | null>(null)
    const [logs, setLogs] = useState<string[]>([])
    const logEndRef = useRef<HTMLDivElement>(null)

    const [mode, setMode] = useState<'topic' | 'manual'>('topic')
    const [manualPrompt, setManualPrompt] = useState('')

    const [customOutputRoot, setCustomOutputRoot] = useState<string | null>(null)
    const outputRoot = customOutputRoot || appConfig?.paths?.datasets_raw || ''

    const [options, setOptions] = useState({
        topic: 'LLM Utils',
        total: 10,
        outputDir: '',  // Will be auto-constructed
        lora: '',
        loraWeight: 1.0,
        trigger: '',
        useTimestamp: false,
        noCaption: false
    })

    const handleBrowse = async () => {
        const paths = await window.api.selectFiles({
            properties: ['openDirectory']
        })
        if (paths && paths.length > 0) {
            setCustomOutputRoot(paths[0])
        }
    }

    const fullOutputPath = customOutputRoot
        ? customOutputRoot
        : `${outputRoot}/${options.topic.toLowerCase().replace(/\s+/g, '_')}`

    const [showLoraDropdown, setShowLoraDropdown] = useState(false)
    const loraDropdownRef = useRef<HTMLDivElement>(null)

    // Filter LoRAs based on input
    const availableLoras = appConfig?.forge?.available_loras || []
    const filteredLoras = availableLoras.filter(lora =>
        lora.toLowerCase().includes(options.lora.toLowerCase())
    )

    // Handle click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (loraDropdownRef.current && !loraDropdownRef.current.contains(event.target as Node)) {
                setShowLoraDropdown(false)
            }
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [])

    const [baseModel, setBaseModel] = useState(appConfig?.forge?.base_model || 'Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors')

    const availableModels = appConfig?.forge?.available_models || [
        'Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors',
        'flux1-dev-fp8.safetensors'
    ]

    useEffect(() => {
        if (appConfig?.forge?.base_model) {
            setBaseModel(appConfig.forge.base_model)
        }
    }, [appConfig])

    useEffect(() => {
        if (window.api?.onDataGenProgress) {
            return window.api.onDataGenProgress((p) => {
                setProgress(p)
                setLogs((prev) => [...prev, `[${p.current}/${p.total}] ${p.status}`])
            })
        }
        return undefined
    }, [])

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [logs])

    // React to sidebar selection
    useEffect(() => {
        if (selection?.path && !isGenerating) {
            const folderName = selection.path.split('/').pop() || '';
            const topicName = folderName.replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
            setOptions(prev => ({ ...prev, topic: topicName }));
        }
    }, [selection]);

    // Check if generation is already running on mount
    useEffect(() => {
        const checkRunning = async () => {
            if (window.api?.isDataGenBusy) {
                const running = await window.api.isDataGenBusy();
                if (running) {
                    setIsGenerating(true);
                }
            }
        };
        checkRunning();
    }, []);

    const handleCopyPath = async () => {
        await navigator.clipboard.writeText(fullOutputPath)
        setCopied(true)
        setTimeout(() => setCopied(false), 2000)
    }

    const handleStart = async () => {
        if (isGenerating) return

        setIsGenerating(true)
        setLogs(['Starting Data Generation...'])
        setProgress({ current: 0, total: options.total, status: 'Initializing...' })

        try {
            // Forge Config
            const forgeConfig = {
                baseUrl: appConfig?.forge?.api_url || 'http://127.0.0.1:7861/sdapi/v1',
                model: baseModel
            }

            const dataGenOptions = mode === 'manual'
                ? { ...options, outputDir: fullOutputPath, manualPrompt }
                : { ...options, outputDir: fullOutputPath }

            const result = await window.api?.startDataGen(dataGenOptions, llmConfig, forgeConfig)
            if (result?.success) {
                setLogs((prev) => [...prev, '--- GENERATION COMPLETE ---'])
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `ERROR: ${error.message}`])
        } finally {
            setIsGenerating(false)
        }
    }

    const handleCancel = async () => {
        try {
            await window.api?.cancelDataGen()
            setLogs((prev) => [...prev, '--- CANCELLED BY USER ---'])
        } catch (error: any) {
            setLogs((prev) => [...prev, `Cancel failed: ${error.message}`])
        }
    }

    return (
        <div className="datagen-container">
            <div className="datagen-grid">
                <div className="datagen-form">
                    <header>
                        <Sparkles size={18} />
                        <span>Generation Configuration</span>
                    </header>

                    <div className="form-content">
                        {/* Base Model Selector */}
                        <div className="form-group">
                            <label><Database size={12} /> Base Model</label>
                            <select
                                value={baseModel}
                                onChange={(e) => setBaseModel(e.target.value)}
                            >
                                {availableModels.map(model => (
                                    <option key={model} value={model}>{model}</option>
                                ))}
                            </select>
                        </div>

                        <div className="divider" />

                        {/* Mode Switcher */}
                        <div className="mode-switcher">
                            <button
                                className={mode === 'topic' ? 'active' : ''}
                                onClick={() => setMode('topic')}
                            >
                                <Sparkles size={14} />
                                <span>Topic Mode</span>
                            </button>
                            <button
                                className={mode === 'manual' ? 'active' : ''}
                                onClick={() => setMode('manual')}
                            >
                                <FileText size={14} />
                                <span>Manual Prompt</span>
                            </button>
                        </div>

                        {/* Topic Mode */}
                        {mode === 'topic' && (
                            <div className="form-group">
                                <label><Tag size={12} /> Topic</label>
                                <input
                                    type="text"
                                    value={options.topic}
                                    onChange={(e) => setOptions({ ...options, topic: e.target.value })}
                                    placeholder="e.g. Cyberpunk City"
                                />
                            </div>
                        )}

                        {/* Manual Prompt Mode */}
                        {mode === 'manual' && (
                            <div className="form-group">
                                <label><FileText size={12} /> Custom Prompt</label>
                                <textarea
                                    value={manualPrompt}
                                    onChange={(e) => setManualPrompt(e.target.value)}
                                    placeholder="Enter your custom SDXL prompt here...\ne.g., a beautiful urban street scene with modern buildings, cars, and pedestrians, realistic, detailed architecture, sunset lighting"
                                    rows={6}
                                />
                            </div>
                        )}

                        <div className="form-group">
                            <label><Layers size={12} /> Total Images</label>
                            <input
                                type="number"
                                value={options.total}
                                onChange={(e) => setOptions({ ...options, total: parseInt(e.target.value) })}
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label><Clock size={12} /> Use Timestamp</label>
                                <div className="checkbox-wrapper">
                                    <input
                                        type="checkbox"
                                        checked={options.useTimestamp}
                                        onChange={(e) => setOptions({ ...options, useTimestamp: e.target.checked })}
                                    />
                                    <span>Filename optimization</span>
                                </div>
                            </div>
                            <div className="form-group">
                                <label><FileText size={12} /> Skip Caption</label>
                                <div className="checkbox-wrapper">
                                    <input
                                        type="checkbox"
                                        checked={options.noCaption}
                                        onChange={(e) => setOptions({ ...options, noCaption: e.target.checked })}
                                    />
                                    <span>Don't generate .txt files</span>
                                </div>
                            </div>
                        </div>

                        <div className="form-group">
                            <label><Folder size={12} /> Output Path (Auto)</label>
                            <div className="file-selector">
                                <input
                                    type="text"
                                    value={fullOutputPath}
                                    readOnly
                                    placeholder="Output path..."
                                />
                                <button onClick={handleCopyPath} title="Copy path">
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                                <button onClick={handleBrowse} title="Browse root folder">
                                    <Folder size={14} />
                                </button>
                            </div>
                        </div>

                        <div className="divider" />

                        <header className="sub-header">
                            <Layers size={14} />
                            <span>LoRA Injection</span>
                        </header>

                        <div className="form-group" ref={loraDropdownRef}>
                            <label>LoRA Model Name</label>
                            <div className="file-selector">
                                <input
                                    type="text"
                                    value={options.lora}
                                    onChange={(e) => {
                                        setOptions({ ...options, lora: e.target.value })
                                        setShowLoraDropdown(true)
                                    }}
                                    onFocus={() => setShowLoraDropdown(true)}
                                    placeholder="Search or type LoRA (e.g. BeautyGirl.safetensors)"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowLoraDropdown(!showLoraDropdown)}
                                    title="Show models"
                                >
                                    <ChevronDown size={14} />
                                </button>

                                {showLoraDropdown && filteredLoras.length > 0 && (
                                    <div className="dropdown-menu">
                                        {filteredLoras.map(lora => (
                                            <div
                                                key={lora}
                                                className="dropdown-item"
                                                onClick={() => {
                                                    setOptions({ ...options, lora })
                                                    setShowLoraDropdown(false)
                                                }}
                                            >
                                                {lora}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>Weight</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    min="0.1"
                                    max="2.0"
                                    value={options.loraWeight}
                                    onChange={(e) => setOptions({ ...options, loraWeight: parseFloat(e.target.value) })}
                                />
                            </div>
                            <div className="form-group">
                                <label>Trigger Word</label>
                                <input
                                    type="text"
                                    value={options.trigger}
                                    onChange={(e) => setOptions({ ...options, trigger: e.target.value })}
                                    placeholder="e.g. FancyStyle"
                                />
                            </div>
                        </div>

                        <div className="actions">
                            <button
                                className={`start-btn ${isGenerating ? 'loading' : ''} ${!outputRoot ? 'disabled' : ''}`}
                                onClick={handleStart}
                                disabled={isGenerating || !outputRoot}
                            >
                                {isGenerating ? <Loader2 className="spinning" size={16} /> : <Play size={16} />}
                                <span>{!outputRoot ? 'Set Output Path' : isGenerating ? 'Generating...' : 'Start Generation'}</span>
                            </button>
                            {isGenerating && (
                                <button
                                    className="cancel-btn"
                                    onClick={handleCancel}
                                >
                                    <StopCircle size={16} />
                                    <span>Cancel</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                <div className="datagen-monitor">
                    <header>
                        <Loader2 size={18} className={isGenerating ? 'spinning' : ''} />
                        <span>Process Monitor</span>
                    </header>

                    <div className="monitor-content">
                        {progress && (
                            <div className="progress-section">
                                <div className="progress-info">
                                    <span>{progress.current} / {progress.total}</span>
                                    <span>{Math.round((progress.current / progress.total) * 100)}%</span>
                                </div>
                                <div className="progress-bar-bg">
                                    <div
                                        className="progress-bar-fill"
                                        style={{ width: `${(progress.current / progress.total) * 100}%` }}
                                    />
                                </div>
                                <div className="progress-status">{progress.status}</div>
                            </div>
                        )}

                        <div className="log-area">
                            {logs.length === 0 ? (
                                <div className="log-empty">Waiting for process start...</div>
                            ) : (
                                logs.map((log, i) => (
                                    <div key={i} className="log-entry">
                                        {log.includes('Saved') ? <CheckCircle size={10} color="#4caf50" /> : log.includes('ERROR') ? <AlertCircle size={10} color="#f44336" /> : <div className="dot" />}
                                        <span>{log}</span>
                                    </div>
                                ))
                            )}
                            <div ref={logEndRef} />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default DataGen
