import React from 'react'
import { Minus, Square, X, Hexagon, ZoomIn, ZoomOut } from 'lucide-react'
import './TitleBar.less'

const TitleBar: React.FC = () => {
    const handleMinimize = () => {
        window.api?.minimize()
    }

    const handleMaximize = () => {
        window.api?.maximize()
    }

    const handleClose = () => {
        window.api?.close()
    }

    const handleZoomIn = () => {
        window.api?.zoomIn()
    }

    const handleZoomOut = () => {
        window.api?.zoomOut()
    }

    return (
        <div className="title-bar">
            <div className="title-bar-drag-region">
                <div className="app-icon">
                    <Hexagon size={14} className="icon-main" />
                </div>
                <div className="app-title">llm-utils - Chat</div>
            </div>

            <div className="window-controls">
                <button className="control-btn zoom-out" onClick={handleZoomOut} title="Zoom Out">
                    <ZoomOut size={14} />
                </button>
                <button className="control-btn zoom-in" onClick={handleZoomIn} title="Zoom In">
                    <ZoomIn size={14} />
                </button>
                <button className="control-btn minimize" onClick={handleMinimize} title="Minimize">
                    <Minus size={14} />
                </button>
                <button className="control-btn maximize" onClick={handleMaximize} title="Maximize">
                    <Square size={12} />
                </button>
                <button className="control-btn close" onClick={handleClose} title="Close">
                    <X size={14} />
                </button>
            </div>
        </div>
    )
}

export default TitleBar
