import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

type Message = {
  role: 'user' | 'ai';
  content: string;
};

function App() {
  const [activeTab, setActiveTab] = useState('ReAct Architecture');
  
  const [messages, setMessages] = useState<{ [key: string]: Message[] }>({
    'ReAct Architecture': [{ role: 'ai', content: 'How can I help you run LangChain tests today?' }],
    'LangGraph Stateful': [{ role: 'ai', content: 'I have a shared lab_session memory.' }],
    'Tools Box Test': [{ role: 'ai', content: 'I can only use @tool book_flight.' }],
    'RAG Evaluation': [{ role: 'ai', content: 'I am tightly bound to the Reginald the Penguin manual context.' }],
    'Enterprise Auto-Coder': [{ role: 'ai', content: 'Phase 07: Enterprise LangGraph loaded. Provide a coding task and I will Loop: Code -> Lint -> Fix -> Commit.' }]
  });
  
  // Independent UUID for Enterprise Auto Coder session
  const [enterpriseThreadId] = useState(crypto.randomUUID());
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => ({
        ...prev,
        [activeTab]: [...prev[activeTab], { role: 'user', content: userMsg }]
    }));
    setIsLoading(true);

    try {
      if (activeTab === 'Enterprise Auto-Coder') {
          // Send to Phase 15 Enterprise AutoCoder via SSE Stream
          const response = await fetch('http://localhost:8001/api/autonomous/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task: userMsg, thread_id: enterpriseThreadId })
          });
          
          if (!response.body) throw new Error("No stream found");
          
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          
          // Append empty placeholder for the incoming stream
          setMessages(prev => ({
              ...prev,
              [activeTab]: [...prev[activeTab], { role: 'ai', content: '> ⏳ *Initializing Enterprise Auto-Coder stream...*' }]
          }));
          
          let currentLog = "";

          while (true) {
              const { value, done } = await reader.read();
              if (done) break;
              
              const chunk = decoder.decode(value, { stream: true });
              const lines = chunk.split('\n\n');
              
              for (const line of lines) {
                  if (line.startsWith('data: ')) {
                      try {
                          const data = JSON.parse(line.substring(6));
                          
                          if (data.type === 'status') {
                              currentLog += `\n> 📡 **Status**: ${data.message}\n`;
                          } else if (data.type === 'node_update') {
                              if (data.node === 'plan_node') {
                                  currentLog += `\n> 🧠 **Planning (Gemma-31B)** *(Iteration ${data.iterations})*\n`;
                                  if (data.plan) {
                                      currentLog += `\n${data.plan}\n`;
                                  }
                                  if (data.test_specs) {
                                      currentLog += `\n> 🧪 **Test Command**: \`${data.test_specs}\`\n`;
                                  }
                              } else if (data.node === 'coder_node') {
                                  currentLog += `\n> 🔄 **Code Gen (Gemma-26B)** *(Iteration ${data.iterations})*\n`;
                              } else if (data.node === 'test_node') {
                                  currentLog += `\n> 🔄 **Validation (Qwen-35B)** *(Iteration ${data.iterations})*\n`;
                                  if (data.validation_status === 'passed') {
                                      currentLog += `> ✅ **Validation Passed**\n`;
                                  } else if (data.lint_errors) {
                                      currentLog += `> ⚠️ **Error Output**:\n\`\`\`\n${data.lint_errors}\n\`\`\`\n`;
                                  }
                              } else if (data.node === 'reflect_node') {
                                  currentLog += `\n> 🤔 **Reflection (Qwen-35B)** *(Iteration ${data.iterations})*\n`;
                                  if (data.reflection_strategy) {
                                      currentLog += `\n${data.reflection_strategy}\n`;
                                  }
                              } else {
                                  currentLog += `\n> 🔄 **Executing Node**: \`${data.node}\` *(Iteration ${data.iterations})*\n`;
                              }
                          } else if (data.type === 'finished') {
                              currentLog += `\n\n✅ **Loop Completed successfully!**\n\n\`\`\`python\n${data.state.code || 'None'}\n\`\`\``;
                          }
                          
                          // Update UI live
                          setMessages(prev => {
                              const updatedChat = [...prev[activeTab]];
                              updatedChat[updatedChat.length - 1] = { role: 'ai', content: currentLog };
                              return { ...prev, [activeTab]: updatedChat };
                          });
                          
                      } catch (e) {
                          console.error("SSE parse error", e);
                      }
                  }
              }
          }
      } else {
          // Send to Phase 06 Legacy Shared LangGraph
          const response = await fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMsg, mode: activeTab })
          });
          const data = await response.json();
          setMessages(prev => ({
              ...prev,
              [activeTab]: [...prev[activeTab], { role: 'ai', content: data.response }]
          }));
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => ({
              ...prev,
              [activeTab]: [...prev[activeTab], { role: 'ai', content: '❌ Error: Failed to reach backend. (Did you run api-dev / enterprise-api-dev?)' }]
          }));
    } finally {
      setIsLoading(false);
    }
  };

  const navItemClass = (tabName: string) => `block border-l pl-4 -ml-px cursor-pointer transition-colors ${
    activeTab === tabName 
      ? 'border-cyan-400 text-cyan-400 font-semibold' 
      : 'border-transparent hover:border-slate-500 text-slate-400 hover:text-slate-300'
  }`;

  return (
    <div className="min-h-screen bg-slate-900 text-slate-400 font-sans selection:bg-cyan-500/30 flex flex-col">
      <header className="sticky top-0 z-40 w-full backdrop-blur flex-none border-b border-slate-800 bg-slate-900/75">
        <div className="w-full">
          <div className="py-4 px-4 sm:px-6 md:px-8">
            <div className="relative flex items-center h-10">
              <a className="mr-3 flex-none w-auto overflow-hidden text-slate-100 font-bold text-xl flex items-center gap-2" href="/">
                <svg className="w-8 h-8 text-cyan-400" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" strokeWidth="2" strokeLinejoin="round"/></svg>
                AutoCoder Lab
              </a>
              <div className="relative flex items-center ml-auto">
                <nav className="text-sm leading-6 font-semibold text-slate-200">
                  <ul className="flex space-x-8">
                    <li><a href="#" className="hover:text-cyan-400 text-cyan-400 transition-colors">AutoCoder Lab</a></li>
                    <li><a href="#" className="hover:text-cyan-400 text-slate-400 transition-colors">Documentation</a></li>
                  </ul>
                </nav>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1 w-full">
        <aside className="hidden lg:block w-[19.5rem] flex-none px-8 py-10">
          <nav className="text-sm leading-6 relative">
            <ul className="space-y-6 lg:space-y-2 border-l border-slate-800">
              <li>
                <div className="block border-l pl-4 -ml-px border-transparent text-slate-200 font-semibold mb-2">Agent Workflows</div>
                <ul className="mt-2 space-y-2 border-l-2 border-transparent">
                  <li onClick={() => setActiveTab('ReAct Architecture')} className={navItemClass('ReAct Architecture')}>ReAct Architecture</li>
                  <li onClick={() => setActiveTab('LangGraph Stateful')} className={navItemClass('LangGraph Stateful')}>LangGraph Stateful</li>
                </ul>
              </li>
              <li className="pt-4" onClick={() => setActiveTab('Tools Box Test')}>
                <div className={navItemClass('Tools Box Test') + " font-semibold"}>Tools Box Test</div>
              </li>
              <li className="pt-4" onClick={() => setActiveTab('RAG Evaluation')}>
                <div className={navItemClass('RAG Evaluation') + " font-semibold"}>RAG Evaluation</div>
              </li>
              <li className="pt-4" onClick={() => setActiveTab('Enterprise Auto-Coder')}>
                <div className={navItemClass('Enterprise Auto-Coder') + " font-semibold text-amber-400"}>Enterprise Auto-Coder</div>
              </li>
            </ul>
          </nav>
        </aside>

        <main className="flex-auto min-w-0 pt-10 pb-24 lg:pb-16 px-4 sm:px-6 xl:px-8">
          <div className="w-[80%] mx-auto max-w-none">
            <header className="mb-9 space-y-1">
              <p className="text-sm font-medium text-cyan-400">Interactive Lab</p>
              <h1 className="text-3xl font-extrabold text-slate-100 tracking-tight">{activeTab}</h1>
            </header>
            
            <div className="prose prose-slate prose-invert max-w-none mb-8 text-slate-300">
              <p>Welcome to the Enterprise AutoCoder Lab. You are currently testing the <strong>{activeTab}</strong> workflow.</p>
            </div>
              
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 shadow-xl">
              <h3 className="text-lg font-medium text-slate-200 mb-6 flex items-center gap-2">
                <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                {activeTab === 'Enterprise Auto-Coder' ? 'Multi-Agent Output' : 'Gemma 4 Interface'}
              </h3>
              
              <div className="space-y-6 max-h-[50vh] overflow-y-auto pr-2">
                {messages[activeTab]?.map((msg, i) => (
                  <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 border 
                      ${msg.role === 'ai' ? 'bg-cyan-500/20 border-cyan-500/30 text-cyan-400' : 'bg-slate-700 border-slate-600 text-slate-300'}`}>
                      <span className="text-sm font-bold">{msg.role === 'ai' ? 'AI' : 'U'}</span>
                    </div>
                    <div className={`p-4 rounded-2xl border text-sm leading-relaxed max-w-[85%]
                      ${msg.role === 'ai' 
                        ? 'bg-slate-700/50 rounded-tl-none border-slate-600/50 text-slate-200' 
                        : 'bg-cyan-900/30 rounded-tr-none border-cyan-800/50 text-cyan-100'}`}>
                      <div className="prose prose-invert prose-sm max-w-none break-words">
                        <ReactMarkdown>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-4 text-cyan-400 text-sm italic">
                     Gemma 4 is running {activeTab}...
                  </div>
                )}
              </div>
              
              <div className="mt-8 flex gap-3 items-center">
                <input 
                  type="text" 
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                  disabled={isLoading}
                  className="w-full bg-slate-900/80 border border-slate-700/80 rounded-lg px-4 py-3 text-slate-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 placeholder-slate-500 text-sm disabled:opacity-50" 
                  placeholder={`Ask Gemma 4 in ${activeTab}...`} 
                />
                <button 
                  onClick={sendMessage}
                  disabled={isLoading}
                  className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold px-6 py-3 rounded-lg transition-colors cursor-pointer text-sm whitespace-nowrap shadow-lg shadow-cyan-500/20 disabled:opacity-50">
                  Send
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
