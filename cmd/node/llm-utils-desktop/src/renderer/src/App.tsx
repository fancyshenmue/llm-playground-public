import { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MessageSquare,
  Settings,
  Terminal,
  Cpu,
  Unplug,
  ChevronRight,
  RefreshCw,
  AlertCircle,
  Edit2,
  ChevronDown,
  Globe,
  Sparkles,
  Zap,
  LineChart,
  DownloadCloud,
  Tag as TagIcon,
  BarChart3
} from 'lucide-react'
import TitleBar from './components/TitleBar/TitleBar'
import Chat from './components/Chat/Chat'
import DataGen from './components/DataGen/DataGen'
import Quant from './components/Quant/Quant'
import QuantAnalyst from './components/QuantAnalyst/QuantAnalyst'
import DataFetch from './components/DataFetch/DataFetch'
import Tag from './components/Tag/Tag'
import Train from './components/Train/Train'
import Rank from './components/Rank/Rank'
import SidebarExplorer from './components/SidebarExplorer/SidebarExplorer'
import './App.less'

type Tab = 'dashboard' | 'chat' | 'datagen' | 'tag' | 'train' | 'rank' | 'datafetch' | 'analyst' | 'quant' | 'settings'

export interface LLMConfig {
  provider: string
  model: string
  baseUrl?: string
}

function App(): React.JSX.Element {
  const [activeTab, setActiveTab] = useState<Tab>('chat')
  const [selection, setSelection] = useState<{ path: string; timestamp: number; isDirectory: boolean } | null>(null)
  const [appConfig, setAppConfig] = useState<any>(null)
  const [llmConfig, setLlmConfig] = useState<LLMConfig>({
    provider: 'ollama',
    model: 'llama3.1:8b',
    baseUrl: 'http://127.0.0.1:11434'
  })

  useEffect(() => {
    const loadConfig = async () => {
      if (window.api?.getConfig) {
        const config = await window.api.getConfig()
        setAppConfig(config)
        if (config.ollama) {
          setLlmConfig({
            provider: 'ollama',
            model: config.ollama.vision_model || 'llama3.1:8b',
            baseUrl: config.ollama.api_url || 'http://127.0.0.1:11434'
          })
        }
      }
    }
    loadConfig()
  }, [])

  const [availableModels, setAvailableModels] = useState<string[]>([])
  const [isLoadingModels, setIsLoadingModels] = useState(false)
  const [modelError, setModelError] = useState<string | null>(null)
  const [isManualModel, setIsManualModel] = useState(false)
  const [isWebMode, setIsWebMode] = useState(false)

  const fetchModels = useCallback(async (): Promise<void> => {
    setIsLoadingModels(true)
    setModelError(null)
    try {
      let models: string[] = []

      if (window.api) {
        setIsWebMode(false)
        models = await window.api.listModels(llmConfig.provider, llmConfig.baseUrl)
      } else {
        // FALLBACK: Web Mode (Direct Fetch to Ollama)
        setIsWebMode(true)
        if (llmConfig.provider === 'ollama') {
          const res = await fetch(`${llmConfig.baseUrl || 'http://localhost:11434'}/api/tags`)
          if (!res.ok) throw new Error(`Ollama Web Mode Error: ${res.statusText}`)
          const data = await res.json()
          models = data.models.map((m: any) => m.name)
        }
      }

      if (Array.isArray(models) && models.length > 0) {
        setAvailableModels(models)
        setIsManualModel(false)
        if (!llmConfig.model || !models.includes(llmConfig.model)) {
          setLlmConfig(prev => ({ ...prev, model: models[0] }))
        }
      } else {
        setAvailableModels([])
        setIsManualModel(true)
      }
    } catch (error: any) {
      console.error('Failed to fetch models:', error)
      setModelError(`${isWebMode ? '[Web Mode] ' : ''}${error.message || 'Connection failed'}`)
      setAvailableModels([])
      setIsManualModel(true)
    } finally {
      setIsLoadingModels(false)
    }
  }, [llmConfig.provider, llmConfig.baseUrl, llmConfig.model, isWebMode])

  useEffect(() => {
    fetchModels()
  }, [llmConfig.provider, llmConfig.baseUrl])

  const handleExplorerClick = (_name: string, fullPath: string, isDirectory: boolean) => {
    setSelection({ path: fullPath, timestamp: Date.now(), isDirectory })
  }

  const activityItems = [
    { id: 'chat', icon: <MessageSquare size={24} />, label: 'Chat' },
    { id: 'datagen', icon: <Sparkles size={24} />, label: 'Data Gen' },
    { id: 'tag', icon: <TagIcon size={24} />, label: 'Tag' },
    { id: 'train', icon: <Cpu size={24} />, label: 'Train' },
    { id: 'rank', icon: <BarChart3 size={24} />, label: 'Rank' },
    { id: 'datafetch', icon: <DownloadCloud size={24} />, label: 'Data Fetch' },
    { id: 'analyst', icon: <Zap size={24} />, label: 'Analyst' },
    { id: 'quant', icon: <LineChart size={24} />, label: 'Quant' },
    { id: 'settings', icon: <Settings size={24} />, label: 'Settings' }
  ]

  return (
    <div className="app-container">
      <TitleBar />
      <div className="main-container">
        {/* Activity Bar */}
        <div className="activity-bar">
          {activityItems.map((item) => (
            <div
              key={item.id}
              className={`activity-item ${activeTab === item.id ? 'active' : ''}`}
              title={item.label}
              onClick={() => setActiveTab(item.id as Tab)}
            >
              {item.icon}
            </div>
          ))}
        </div>

        {/* Side Bar */}
        <div className="side-bar">
          <header>{activeTab}</header>
          <div className="side-bar-content">
            {activeTab === 'chat' && (
              <div className="side-bar-section">
                <div className="section-title">
                  <ChevronRight size={14} />
                  CONFIGURATION
                </div>
                <div className="config-form">
                  <div className="form-group">
                    <label>Provider</label>
                    <select
                      value={llmConfig.provider}
                      onChange={(e) => setLlmConfig({ ...llmConfig, provider: e.target.value })}
                    >
                      <option value="ollama">Ollama</option>
                      <option value="openai">OpenAI (planned)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Base URL</label>
                    <input
                      type="text"
                      value={llmConfig.baseUrl}
                      onChange={(e) => setLlmConfig({ ...llmConfig, baseUrl: e.target.value })}
                      placeholder="http://localhost:11434"
                    />
                  </div>

                  <div className="form-group">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <label>Model</label>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <button
                          className="icon-button"
                          onClick={() => setIsManualModel(!isManualModel)}
                          title={isManualModel ? "Switch to selection" : "Switch to manual input"}
                        >
                          {isManualModel ? <ChevronDown size={12} /> : <Edit2 size={12} />}
                        </button>
                        <button
                          className="icon-button"
                          onClick={fetchModels}
                          title="Refresh models"
                          disabled={isLoadingModels}
                        >
                          <RefreshCw size={12} className={isLoadingModels ? 'spinning' : ''} />
                        </button>
                      </div>
                    </div>

                    {isManualModel ? (
                      <input
                        type="text"
                        value={llmConfig.model}
                        onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
                        placeholder="e.g. llama3"
                      />
                    ) : (
                      <div className="select-wrapper">
                        <select
                          value={llmConfig.model}
                          onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
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
                    )}

                    {modelError && (
                      <div className="error-text">
                        <AlertCircle size={10} />
                        <span>{modelError}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="section-title" style={{ marginTop: '20px' }}>
                  <ChevronRight size={14} />
                  SESSIONS
                </div>
                <div style={{ padding: '0 20px', fontSize: '12px', opacity: 0.5, fontStyle: 'italic' }}>
                  No active sessions
                </div>
              </div>
            )}
            {activeTab === 'quant' && (
              <div className="side-bar-section">
                <div className="section-title">
                  <ChevronRight size={14} />
                  QUANT TOOLS
                </div>
                <div style={{ padding: '10px 20px', fontSize: '12px', color: '#888' }}>
                  Generate and manage your TradingView strategies with ease.
                </div>
              </div>
            )}
            {activeTab === 'analyst' && (
              <div className="side-bar-section">
                <div className="section-title">
                  <ChevronRight size={14} />
                  ANALYST TOOLS
                </div>
                <div style={{ padding: '10px 20px', fontSize: '12px', color: '#888' }}>
                  Distill market data into powerful prompts for LLMs.
                </div>
              </div>
            )}
            {activeTab === 'datagen' && (
              <div className="side-bar-section no-padding">
                <div className="section-title">
                  <ChevronRight size={14} />
                  EXPLORER
                </div>
                <SidebarExplorer
                  title="Raw Datasets"
                  rootPath={appConfig?.paths?.datasets_raw || ''}
                  onFolderClick={handleExplorerClick}
                />
              </div>
            )}
            {activeTab === 'datafetch' && (
              <div className="side-bar-section">
                <div className="section-title">
                  <ChevronRight size={14} />
                  DATA FETCH
                </div>
                <div style={{ padding: '10px 20px', fontSize: '12px', color: '#888' }}>
                  Download multi-timeframe OHLCV data from cryptocurrency exchanges.
                </div>
              </div>
            )}
            {activeTab === 'tag' && (
              <div className="side-bar-section no-padding">
                <div className="section-title">
                  <ChevronRight size={14} />
                  EXPLORER
                </div>
                <SidebarExplorer
                  title="Source Images"
                  rootPath={appConfig?.paths?.datasets_raw || ''}
                  onFolderClick={handleExplorerClick}
                />
                <SidebarExplorer
                  title="Tagged Outputs"
                  rootPath={appConfig?.paths?.datasets_tagged || ''}
                  onFolderClick={handleExplorerClick}
                />
              </div>
            )}
            {activeTab === 'train' && (
              <div className="side-bar-section no-padding">
                <div className="section-title">
                  <ChevronRight size={14} />
                  EXPLORER
                </div>
                <SidebarExplorer
                  title="Training Images"
                  rootPath={appConfig?.paths?.train_image_dir || ''}
                  onFolderClick={handleExplorerClick}
                  showFiles={true}
                />
              </div>
            )}
            {activeTab === 'rank' && (
              <div className="side-bar-section no-padding">
                <div className="section-title">
                  <ChevronRight size={14} />
                  EXPLORER
                </div>
                <SidebarExplorer
                  title="Images to Rank"
                  rootPath={appConfig?.defaults?.rank?.images_root || ''}
                  onFolderClick={handleExplorerClick}
                />
              </div>
            )}
          </div>
        </div>

        {/* Main Content Area */}
        <div className="main-content">
          <div className="content-header">
            <div className="breadcrumb">
              <span>llm-utils</span>
              <span style={{ opacity: 0.4 }}>/</span>
              <span>{activeTab}</span>
            </div>
          </div>
          <div className="viewport">
            {isWebMode && (
              <div className="web-mode-banner">
                <Globe size={14} />
                <span>Running in Web Compatibility Mode. Use Electron for best experience.</span>
              </div>
            )}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="full-height"
              >
                {activeTab === 'chat' && <Chat config={llmConfig} />}
                {activeTab === 'datagen' && <DataGen llmConfig={llmConfig} selection={selection} appConfig={appConfig} />}
                {activeTab === 'quant' && <Quant llmConfig={llmConfig} />}
                {activeTab === 'analyst' && (
                  <QuantAnalyst
                    llmConfig={llmConfig}
                    availableModels={availableModels}
                    isLoadingModels={isLoadingModels}
                  />
                )}
                {activeTab === 'datafetch' && <DataFetch />}
                {activeTab === 'tag' && <Tag selection={selection} appConfig={appConfig} />}
                {activeTab === 'train' && <Train selection={selection} appConfig={appConfig} />}
                {activeTab === 'rank' && <Rank llmConfig={llmConfig} selection={selection} />}
                {activeTab !== 'chat' && activeTab !== 'datagen' && activeTab !== 'quant' && activeTab !== 'analyst' && activeTab !== 'datafetch' && activeTab !== 'tag' && activeTab !== 'train' && activeTab !== 'rank' && (
                  <div className="placeholder-view">
                    <Terminal size={64} />
                    <div style={{ fontSize: '20px' }}>{activeTab.toUpperCase()} IN PROGRESS</div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="status-bar">
        <div className="status-left">
          <div className="status-item">
            <Cpu size={14} />
            <span>{llmConfig.provider}: {llmConfig.model || 'none'}</span>
          </div>
        </div>
        <div className="status-right">
          <div className="status-item">
            <span>{llmConfig.baseUrl}</span>
            <span>UTF-8</span>
            {isWebMode ? <Globe size={14} /> : <Unplug size={14} />}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
