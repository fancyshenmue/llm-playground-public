import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Bot, User, Loader2 } from 'lucide-react'
import { LLMConfig } from '../../App'
import './Chat.less'

interface Message {
    role: 'user' | 'assistant'
    content: string
}

interface ChatProps {
    config: LLMConfig
}

export default function Chat({ config }: ChatProps): React.JSX.Element {
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const messagesEndRef = useRef<HTMLDivElement>(null)

    const scrollToBottom = (): void => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async (): Promise<void> => {
        if (!input.trim() || isLoading) return

        const userMsg: Message = { role: 'user', content: input }
        setMessages((prev) => [...prev, userMsg])
        setInput('')
        setIsLoading(true)

        try {
            let response: string
            // Check if we are in Electron or Web Mode
            if (window.api) {
                response = await window.api.chat([...messages, userMsg], config)
            } else {
                // FALLBACK: Web Mode (Direct Fetch to Ollama)
                if (config.provider === 'ollama') {
                    const res = await fetch(`${config.baseUrl || 'http://localhost:11434'}/api/chat`, {
                        method: 'POST',
                        body: JSON.stringify({
                            model: config.model,
                            messages: [...messages, userMsg].map(m => ({
                                role: m.role,
                                content: m.content
                            })),
                            stream: false
                        })
                    })
                    if (!res.ok) throw new Error(`Ollama Web Mode Error: ${res.statusText}`)
                    const data = await res.json()
                    response = data.message.content
                } else {
                    throw new Error('Web Mode only supports Ollama for now.')
                }
            }
            setMessages((prev) => [...prev, { role: 'assistant', content: response }])
        } catch (error: any) {
            setMessages((prev) => [
                ...prev,
                { role: 'assistant', content: `Error: ${error.message}` }
            ])
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className="chat-container">
            <div className="messages-list">
                {messages.length === 0 && (
                    <div className="empty-state">
                        <Bot size={48} style={{ opacity: 0.1, marginBottom: '20px' }} />
                        <div style={{ opacity: 0.3 }}>Ready to assist with {config.model || '...'}</div>
                    </div>
                )}
                <AnimatePresence initial={false}>
                    {messages.map((msg, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`message-wrapper ${msg.role}`}
                        >
                            <div className="avatar">
                                {msg.role === 'assistant' ? <Bot size={18} /> : <User size={18} />}
                            </div>
                            <div className="content">
                                <div className="bubble">{msg.content}</div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
                {isLoading && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="message-wrapper assistant loading"
                    >
                        <div className="avatar">
                            <Bot size={18} />
                        </div>
                        <div className="content">
                            <div className="bubble">
                                <Loader2 className="spinner" size={16} />
                            </div>
                        </div>
                    </motion.div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
                <div className="input-wrapper">
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        placeholder={`Ask anything using ${config.model}...`}
                        disabled={isLoading}
                    />
                </div>
                <button onClick={handleSend} disabled={isLoading || !input.trim()}>
                    <Send size={18} />
                </button>
            </div>
        </div>
    )
}
