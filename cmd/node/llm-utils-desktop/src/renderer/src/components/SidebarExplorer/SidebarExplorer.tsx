import React, { useState, useEffect } from 'react';
import { Folder, FileText, ChevronRight, ChevronDown, RefreshCw } from 'lucide-react';
import './SidebarExplorer.less';

interface SidebarItem {
    name: string;
    isDirectory: boolean;
}

interface SidebarExplorerProps {
    title: string;
    rootPath: string;
    showFiles?: boolean;
    onFolderClick?: (name: string, fullPath: string, isDirectory: boolean) => void;
    refreshTrigger?: any;
}

const SidebarExplorer: React.FC<SidebarExplorerProps> = ({ title, rootPath, showFiles = false, onFolderClick, refreshTrigger }) => {
    const [items, setItems] = useState<SidebarItem[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isExpanded, setIsExpanded] = useState(true);

    const fetchItems = async () => {
        if (!rootPath) return;
        setIsLoading(true);
        try {
            const data = await window.api.listItems(rootPath, showFiles);
            setItems(data);
        } catch (error) {
            console.error('Failed to fetch explorer items:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchItems();
    }, [rootPath, showFiles, refreshTrigger]);

    return (
        <div className="sidebar-explorer">
            <div className="explorer-header" onClick={() => setIsExpanded(!isExpanded)}>
                <div className="header-left">
                    {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    <span>{title.toUpperCase()}</span>
                </div>
                <div className="header-actions">
                    <button
                        onClick={(e) => { e.stopPropagation(); fetchItems(); }}
                        title="Refresh"
                        disabled={isLoading}
                    >
                        <RefreshCw size={12} className={isLoading ? 'spinning' : ''} />
                    </button>
                </div>
            </div>

            {isExpanded && (
                <div className="explorer-content">
                    {items.length === 0 && !isLoading ? (
                        !rootPath ? (
                            <div className="empty-state">Path not configured</div>
                        ) : (
                            <div className="empty-state">No items found</div>
                        )
                    ) : (
                        items.map((item) => (
                            <div
                                key={item.name}
                                className={`folder-item ${item.isDirectory ? 'dir' : 'file'}`}
                                onClick={() => onFolderClick?.(item.name, `${rootPath}/${item.name}`, item.isDirectory)}
                            >
                                {item.isDirectory ? <Folder size={14} /> : <FileText size={14} />}
                                <span title={item.name}>{item.name}</span>
                            </div>
                        ))
                    )}
                    {isLoading && <div className="loading-state">Loading...</div>}
                </div>
            )}
        </div>
    );
};

export default SidebarExplorer;
