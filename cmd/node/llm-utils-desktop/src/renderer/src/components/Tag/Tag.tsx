import { useState, useEffect, useRef } from 'react';
import { Tag as TagIcon, Folder, Play, StopCircle, Loader2, Copy, Check, Terminal } from 'lucide-react';
import './Tag.less';

interface TagProps {
    selection?: { path: string; timestamp: number; isDirectory: boolean } | null;
    appConfig?: any;
}

const Tag: React.FC<TagProps> = ({ selection, appConfig }) => {
    const [imageDir, setImageDir] = useState('');
    const [model, setModel] = useState(appConfig?.defaults?.tag?.model || 'WD v1.4 ConVNext V2');
    const [generalThreshold, setGeneralThreshold] = useState(appConfig?.defaults?.tag?.general_threshold || 0.35);
    const [characterThreshold, setCharacterThreshold] = useState(appConfig?.defaults?.tag?.character_threshold || 0.35);
    const [isTagging, setIsTagging] = useState(false);
    const [copied, setCopied] = useState(false);
    const [logs, setLogs] = useState<string[]>([]);
    const [progress, setProgress] = useState<{
        current?: number;
        total?: number;
        status: string;
    } | null>(null);

    // Promotion State
    const [repeats, setRepeats] = useState(10);
    const [targetTopicName, setTargetTopicName] = useState('');
    const [isPromoting, setIsPromoting] = useState(false);

    const logRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom of logs
    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [logs]);

    const availableModels = [
        'WD v1.4 ConVNext V2',
        'WD v1.4 ViT V2',
        'WD v1.4 SwinV2 V2'
    ];

    useEffect(() => {
        if (window.api?.onTagProgress) {
            const cleanup = window.api.onTagProgress((p) => {
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

                        return updatedLogs.slice(-1000);
                    });
                }

                if (p.current !== undefined && p.total !== undefined) {
                    setProgress({
                        current: p.current,
                        total: p.total,
                        status: p.status
                    });
                }
            });
            return cleanup;
        }
        return undefined;
    }, []);

    // Extract topic name from image path
    useEffect(() => {
        if (imageDir) {
            const parts = imageDir.split(/[/\\]/);
            const folderName = parts[parts.length - 1];
            if (folderName && !targetTopicName) {
                setTargetTopicName(folderName);
            }
        }
    }, [imageDir]);

    // React to appConfig updates
    useEffect(() => {
        if (appConfig?.defaults?.tag) {
            setModel(appConfig.defaults.tag.model || 'WD v1.4 ConVNext V2');
            setGeneralThreshold(appConfig.defaults.tag.general_threshold || 0.35);
            setCharacterThreshold(appConfig.defaults.tag.character_threshold || 0.35);
        }
    }, [appConfig]);

    // React to sidebar selection
    useEffect(() => {
        if (selection?.path && !isTagging) {
            setImageDir(selection.path);
        }
    }, [selection]);

    // Check if tagging is already running on mount
    useEffect(() => {
        const checkRunning = async () => {
            if (window.api?.isTaggingRunning) {
                const running = await window.api.isTaggingRunning();
                if (running) {
                    setIsTagging(true);
                }
            }
        };
        checkRunning();
    }, []);

    const handleSelectDirectory = async () => {
        try {
            const paths = await window.api?.selectFiles({
                properties: ['openDirectory']
            });
            if (paths && paths.length > 0) {
                setImageDir(paths[0]);
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `Error selecting directory: ${error.message}`]);
        }
    };

    const handleCopyPath = async () => {
        if (imageDir) {
            await navigator.clipboard.writeText(imageDir);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const handleStart = async () => {
        if (!imageDir) {
            setLogs(['Error: Please select an image directory']);
            return;
        }

        setIsTagging(true);
        setLogs([]);
        setProgress(null);

        try {
            // Map UI model name to HuggingFace repo ID
            const modelMap: Record<string, string> = {
                'WD v1.4 ConVNext V2': 'SmilingWolf/wd-v1-4-convnextv2-tagger-v2',
                'WD v1.4 ViT V2': 'SmilingWolf/wd-v1-4-vit-tagger-v2',
                'WD v1.4 SwinV2 V2': 'SmilingWolf/wd-v1-4-swinv2-tagger-v2'
            };

            const options = {
                path: imageDir,  // TagService expects 'path' not 'imageDir'
                model: modelMap[model] || 'SmilingWolf/wd-v1-4-convnextv2-tagger-v2',
                threshold: generalThreshold,  // Main threshold
                generalThreshold,
                characterThreshold,
                batchSize: 1,
                maxWorkers: 2,
                recursive: false,
                debug: true,
                undesired: ''  // Empty string for now, can be made configurable later
            };

            const result = await window.api?.startTagging(options);
            if (result?.success) {
                setLogs((prev) => [...prev, '✅ Tagging completed successfully!']);
            } else {
                setLogs((prev) => [...prev, `❌ Tagging failed: ${result?.error}`]);
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `❌ Error: ${error.message}`]);
        } finally {
            setIsTagging(false);
        }
    };

    const handleCancel = async () => {
        try {
            await window.api?.cancelTagging();
            setLogs((prev) => [...prev, '--- CANCELLED BY USER ---']);
        } catch (error: any) {
            setLogs((prev) => [...prev, `Cancel failed: ${error.message}`]);
        }
    };

    const handlePromote = async () => {
        if (!imageDir || !targetTopicName) return;

        setIsPromoting(true);
        try {
            const result = await window.api?.promoteDataset(imageDir, targetTopicName, repeats);
            if (result?.success) {
                setLogs((prev) => [
                    ...prev,
                    `✅ Dataset promoted to: ${result.destPath}`,
                    `👉 You can now go to "Train" tab and select this directory.`
                ]);
                // Set imageDir to empty so they don't promote twice to the same place
                setImageDir('');
                setTargetTopicName('');
            } else {
                setLogs((prev) => [...prev, `❌ Promotion failed: ${result?.error}`]);
            }
        } catch (error: any) {
            setLogs((prev) => [...prev, `❌ Error: ${error.message}`]);
        } finally {
            setIsPromoting(false);
        }
    };

    return (
        <div className="tag-container">
            <div className="tag-grid">
                <div className="tag-form">
                    <header>
                        <TagIcon size={18} />
                        <span>WD14 Tagger Configuration</span>
                    </header>

                    <div className="form-content">
                        <div className="form-group">
                            <label><Folder size={12} /> Image Directory</label>
                            <div className="file-selector">
                                <input
                                    type="text"
                                    value={imageDir}
                                    placeholder="Select image directory..."
                                    onChange={(e) => setImageDir(e.target.value)}
                                />
                                <button onClick={handleCopyPath} disabled={!imageDir} title="Copy path">
                                    {copied ? <Check size={14} /> : <Copy size={14} />}
                                </button>
                                <button onClick={handleSelectDirectory}>Browse</button>
                            </div>
                        </div>

                        <div className="divider" />

                        <header className="sub-header">
                            <TagIcon size={14} />
                            <span>Model Settings</span>
                        </header>

                        <div className="form-group">
                            <label>Model</label>
                            <select
                                value={model}
                                onChange={(e) => setModel(e.target.value)}
                            >
                                {availableModels.map((m) => (
                                    <option key={m} value={m}>{m}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-row">
                            <div className="form-group">
                                <label>General Threshold</label>
                                <input
                                    type="number"
                                    step="0.05"
                                    min="0"
                                    max="1"
                                    value={generalThreshold}
                                    onChange={(e) => setGeneralThreshold(parseFloat(e.target.value))}
                                />
                            </div>
                            <div className="form-group">
                                <label>Character Threshold</label>
                                <input
                                    type="number"
                                    step="0.05"
                                    min="0"
                                    max="1"
                                    value={characterThreshold}
                                    onChange={(e) => setCharacterThreshold(parseFloat(e.target.value))}
                                />
                            </div>
                        </div>

                        <div className="divider" />

                        <div className="actions">
                            <button
                                className={`start-btn ${isTagging ? 'loading' : ''}`}
                                onClick={handleStart}
                                disabled={isTagging || !imageDir}
                            >
                                {isTagging ? <Loader2 className="spinning" size={16} /> : <Play size={16} />}
                                <span>{isTagging ? 'Tagging...' : 'Start Tagging'}</span>
                            </button>
                            {isTagging && (
                                <button
                                    className="cancel-btn"
                                    onClick={handleCancel}
                                >
                                    <StopCircle size={16} />
                                    <span>Cancel</span>
                                </button>
                            )}
                        </div>

                        {/* Promotion Section - Show when tagging is done or when a directory is loaded */}
                        {imageDir && !isTagging && (
                            <>
                                <div className="divider" />
                                <header className="sub-header">
                                    <Folder size={14} />
                                    <span>Prepare for Training (Promotion)</span>
                                </header>
                                <div className="promotion-panel">
                                    <div className="form-row">
                                        <div className="form-group">
                                            <label title="How many times the trainer looks at each image per epoch. Total Steps = Images * Repeats.">
                                                Repeats <span className="help-icon">?</span>
                                            </label>
                                            <input
                                                type="number"
                                                min="1"
                                                value={repeats}
                                                onChange={(e) => setRepeats(parseInt(e.target.value) || 1)}
                                            />
                                        </div>
                                        <div className="form-group flex-2">
                                            <label>Topic Name</label>
                                            <input
                                                type="text"
                                                value={targetTopicName}
                                                placeholder="e.g. country_road"
                                                onChange={(e) => setTargetTopicName(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <button
                                        className={`promote-btn ${isPromoting ? 'loading' : ''}`}
                                        onClick={handlePromote}
                                        disabled={isPromoting || !targetTopicName}
                                    >
                                        {isPromoting ? <Loader2 className="spinning" size={16} /> : <Folder size={16} />}
                                        <span>Move to Training Folder</span>
                                    </button>
                                    <p className="promotion-hint">
                                        Renames to <b>{repeats}_{targetTopicName || 'topic'}</b> and moves to training root.
                                    </p>
                                </div>
                            </>
                        )}
                    </div>
                </div>

                {/* Monitor Section */}
                <div className="tag-monitor">
                    <header>
                        <Loader2 size={18} className={isTagging ? 'spinning' : ''} />
                        <span>Tagging Monitor</span>
                    </header>

                    <div className="monitor-content">
                        {/* Progress Display */}
                        {progress && progress.current !== undefined && progress.total !== undefined && (
                            <div className="progress-section">
                                <div className="progress-row">
                                    <span className="label">Progress:</span>
                                    <span className="value">{progress.current} / {progress.total}</span>
                                    <div className="progress-bar-bg">
                                        <div
                                            className="progress-bar-fill"
                                            style={{
                                                width: `${(progress.current / progress.total) * 100}%`
                                            }}
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Logs */}
                        <div className="log-area" ref={logRef}>
                            {logs.length === 0 ? (
                                <div className="log-empty">
                                    <Terminal size={32} />
                                    <span>No tagging logs yet. Select a directory and start tagging.</span>
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

export default Tag;
