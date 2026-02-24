import { useState, useEffect, useRef } from 'react';
import { Database, Play, StopCircle, Loader2, FileText, Copy, Check, Terminal } from 'lucide-react';
import './Train.less';

interface TrainProps {
    selection?: { path: string; timestamp: number; isDirectory: boolean } | null;
    appConfig?: any;
}

const Train: React.FC<TrainProps> = ({ selection, appConfig }) => {
    // We could use appConfig?.paths?.lora_project_root etc.
    const [configPath, setConfigPath] = useState('');
    const [isTraining, setIsTraining] = useState(false);
    const [copied, setCopied] = useState(false);
    const [logsCopied, setLogsCopied] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [progress, setProgress] = useState<{
        epoch?: number;
        maxEpochs?: number;
        step?: number;
        maxSteps?: number;
        loss?: number;
    } | null>(null);

    const logRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of logs
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [logs]);

    useEffect(() => {
        if (window.api?.onTrainProgress) {
            const cleanup = window.api.onTrainProgress((p) => {
                if (p.status) {
                    setLogs((prev) => {
                        const newText = p.status!;
                        // Strip ANSI escape codes
                        const cleanText = newText.replace(/[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g, '');

                        let updatedLogs = [...prev];
                        const lines = cleanText.split(/\n/);

                        lines.forEach((line, idx) => {
                            if (line.includes('\r')) {
                                const subParts = line.split('\r');
                                const finalState = subParts[subParts.length - 1];
                                if (finalState.length > 0) {
                                    if (updatedLogs.length > 0 && idx === 0 && !newText.startsWith('\n')) {
                                        updatedLogs[updatedLogs.length - 1] = finalState;
                                    } else {
                                        updatedLogs.push(finalState);
                                    }
                                }
                            } else if (line.length > 0) {
                                updatedLogs.push(line);
                            }
                        });

                        return updatedLogs.slice(-2000);
                    });
                }

                if (p.epoch !== undefined || p.step !== undefined || p.loss !== undefined) {
                    setProgress({
                        epoch: p.epoch,
                        maxEpochs: p.maxEpochs,
                        step: p.step,
                        maxSteps: p.maxSteps,
                        loss: p.loss
                    });
                }
            });
            return cleanup;
        }
        return undefined;
    }, []);

    // React to sidebar selection
    useEffect(() => {
        if (!selection?.path || isTraining) return;

        if (!selection.isDirectory) {
            if (selection.path.toLowerCase().endsWith('.json')) {
                setConfigPath(selection.path);
            }
        } else {
            // It's a directory, try to find a .json file inside
            const findConfig = async () => {
                try {
                    const items = await window.api.listItems(selection.path, true);
                    const jsonFile = items.find(item => !item.isDirectory && item.name.toLowerCase().endsWith('.json'));
                    if (jsonFile) {
                        setConfigPath(`${selection.path}/${jsonFile.name}`);
                    }
                } catch (error) {
                    console.error('Failed to auto-find config in directory:', error);
                }
            };
            findConfig();
        }
    }, [selection]);

    // Check if training is already running on mount
    useEffect(() => {
        const checkRunning = async () => {
            if (window.api?.isTrainingRunning) {
                const running = await window.api.isTrainingRunning();
                if (running) {
                    setIsTraining(true);
                }
            }
        };
        checkRunning();
    }, []);

    const handleStart = async () => {
        if (!configPath) {
            setLogs(['Error: Please select a config file']);
            return;
        }

        setIsTraining(true);
        setLogs([]);
        setProgress(null);

        try {
            const result = await window.api?.startTraining(configPath);
            if (result?.success) {
                setLogs((prev) => [...prev, '✅ Training completed successfully!']);
            } else {
                setLogs((prev) => [...prev, `❌ Training failed: ${result?.error}`]);
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `❌ Error: ${error.message}`]);
        } finally {
            setIsTraining(false);
        }
    };

    const handleCancel = async () => {
        try {
            await window.api?.cancelTraining();
            setLogs((prev) => [...prev, '🛑 Training cancelled by user']);
            setIsTraining(false);
        } catch (error: any) {
            setLogs((prev) => [...prev, `❌ Cancel failed: ${error.message}`]);
        }
    };

    const handleCopyPath = async () => {
        if (configPath) {
            await navigator.clipboard.writeText(configPath);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleCopyLogs = async () => {
        if (logs.length > 0) {
            await navigator.clipboard.writeText(logs.join('\n'));
            setLogsCopied(true);
            setTimeout(() => setLogsCopied(false), 2000);
        }
    };

    const handleSelectConfig = async () => {
        try {
            const paths = await window.api?.selectFiles({
                filters: [{ name: 'JSON Config', extensions: ['json'] }],
                properties: ['openFile']
            });
            if (paths && paths.length > 0) {
                setConfigPath(paths[0]);
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `Error selecting file: ${error.message}`]);
        }
    };

    return (
        <div className="train-container">
            <div className="train-grid">
                <div className="train-form">
                    <header>
                        <Database size={18} />
                        <span>Training Configuration</span>
                    </header>

                    <div className="form-content">
                        <div className="form-group">
                            <label><FileText size={12} /> Config File</label>
                            <div className="file-selector">
                                <input
                                    type="text"
                                    value={configPath}
                                    onChange={(e) => setConfigPath(e.target.value)}
                                    placeholder="Select training config JSON..."
                                />
                                <button onClick={handleCopyPath} disabled={!configPath} title="Copy path">
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                                <button onClick={handleSelectConfig}>Browse</button>
                            </div>
                        </div>

                        <div className="divider" />

                        <div className="actions">
                            <button
                                className={`start-btn ${isTraining ? 'loading' : ''}`}
                                onClick={handleStart}
                                disabled={isTraining || !configPath}
                            >
                                {isTraining ? <Loader2 className="spinning" size={16} /> : <Play size={16} />}
                                <span>{isTraining ? 'Training...' : 'Start Training'}</span>
                            </button>
                            {isTraining && (
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

                {/* Monitoring Section */}
                <div className="train-monitor">
                    <header>
                        <Loader2 size={18} className={isTraining ? 'spinning' : ''} />
                        <span>Training Monitor</span>
                        <button
                            onClick={handleCopyLogs}
                            disabled={logs.length === 0}
                            className="copy-logs-btn"
                            title="Copy all logs"
                        >
                            {logsCopied ? <Check size={14} /> : <Copy size={14} />}
                        </button>
                    </header>

                    <div className="monitor-content">
                        {/* Progress Display */}
                        {progress && (
                            <div className="progress-section">
                                {progress.epoch !== undefined && (
                                    <div className="progress-row">
                                        <span className="label">Epoch:</span>
                                        <span className="value">{progress.epoch} / {progress.maxEpochs}</span>
                                    </div>
                                )}
                                {progress.step !== undefined && (
                                    <div className="progress-row">
                                        <span className="label">Step:</span>
                                        <span className="value">{progress.step} / {progress.maxSteps}</span>
                                        <div className="progress-bar-bg">
                                            <div
                                                className="progress-bar-fill"
                                                style={{
                                                    width: `${((progress.step || 0) / (progress.maxSteps || 1)) * 100}%`
                                                }}
                                            />
                                        </div>
                                    </div>
                                )}
                                {progress.loss !== undefined && (
                                    <div className="progress-row">
                                        <span className="label">Loss:</span>
                                        <span className="value loss">{progress.loss.toFixed(6)}</span>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Logs */}
                        <div className="log-area" ref={logRef}>
                            {logs.length === 0 ? (
                                <div className="log-empty">
                                    <Terminal size={32} />
                                    <span>No training logs yet. Start training to see progress.</span>
                                </div>
                            ) : (
                                logs.map((log, idx) => (
                                    <div key={idx} className="log-entry">
                                        <div className="dot" />
                                        <span>{log}</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Train;
