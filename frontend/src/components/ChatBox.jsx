import React, { useRef, useEffect } from 'react';

// ── Icons (Custom SVGs to avoid crashing lucide-react) ──
const IconSend = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
);
const IconUser = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
);
const IconBot = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
);
const IconPaperclip = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.51a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>
);
const IconChevronDown = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
);
const IconChevronUp = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m18 15-6-6-6 6"/></svg>
);

const SourceSnippet = ({ source }) => {
  const [isOpen, setIsOpen] = React.useState(false);

  return (
    <div className="mt-3 border border-cyber-border/30 rounded-xl overflow-hidden bg-cyber-dark/30">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 flex items-center justify-between hover:bg-cyber-teal/5 transition-all text-[11px] font-mono text-gray-400"
      >
        <span className="flex items-center gap-2">
          <span className="text-cyber-teal"><IconPaperclip /></span>
          <span className="text-cyber-teal/80">{source.file_path}</span>
          <span>(Lines {source.start_line}-{source.end_line})</span>
        </span>
        {isOpen ? <IconChevronUp /> : <IconChevronDown />}
      </button>
      
      {isOpen && (
        <div className="border-t border-cyber-border/20 p-4 text-[12px] bg-black/40 overflow-x-auto">
          <pre className="font-mono text-gray-300">
            <code>{source.text}</code>
          </pre>
        </div>
      )}
    </div>
  );
};

const ChatBox = ({ chatHistory, userInput, setUserInput, onSend, isLoading }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatHistory]);

  return (
    <main className="flex-1 flex flex-col h-full bg-cyber-black relative overflow-hidden">
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-cyber-teal/5 blur-[120px] rounded-full -mr-64 -mt-64" />
      
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 z-10">
        {chatHistory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center space-y-4 opacity-70">
            <span className="text-cyber-teal mb-2"><IconBot /></span>
            <div>
              <p className="text-xl font-bold font-mono text-white tracking-tighter">REPOMINDS <span className="text-cyber-teal">IS READY</span></p>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest">Index a repository to start chatting</p>
            </div>
          </div>
        ) : (
          chatHistory.map((msg, i) => (
            <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`mt-1 p-2 rounded-lg h-fit bg-cyber-dark border ${msg.role === 'user' ? 'border-gray-700' : 'border-cyber-teal/20'}`}>
                {msg.role === 'user' ? <span className="text-gray-400"><IconUser /></span> : <span className="text-cyber-teal"><IconBot /></span>}
              </div>
              
              <div className={`max-w-[75%] space-y-2`}>
                <div className={`p-4 rounded-2xl ${
                  msg.role === 'user' 
                  ? 'bg-cyber-dark border border-gray-800 text-gray-200' 
                  : 'bg-cyber-dark/50 border border-cyber-border/10 text-gray-200 backdrop-blur-sm'
                }`}>
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content || msg.answer}</p>
                  
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-cyber-border/10">
                      <p className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-2">Sources</p>
                      {msg.sources.map((src, idx) => (
                        <SourceSnippet key={idx} source={src} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex gap-4 animate-pulse">
            <div className="mt-1 p-2 rounded-lg h-fit bg-cyber-dark border border-cyber-teal/20">
              <span className="text-cyber-teal opacity-50"><IconBot /></span>
            </div>
            <div className="bg-cyber-dark/30 border border-cyber-border/10 p-4 rounded-2xl">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-cyber-teal rounded-full animate-bounce delay-75"></span>
                <span className="w-1.5 h-1.5 bg-cyber-teal rounded-full animate-bounce delay-150"></span>
                <span className="w-1.5 h-1.5 bg-cyber-teal rounded-full animate-bounce delay-300"></span>
                <span className="text-[10px] uppercase font-mono text-cyber-teal/50 ml-2">Repominds is Thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="p-6 border-t border-cyber-border bg-cyber-black z-10">
        <div className="relative group">
          <input
            type="text"
            placeholder="Ask about the codebase..."
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !isLoading && onSend()}
            disabled={isLoading}
            className="w-full bg-cyber-dark border border-cyber-border rounded-2xl py-4 pl-6 pr-16 text-sm focus:outline-none focus:border-cyber-teal/50 transition-all text-gray-200 shadow-xl placeholder:text-gray-600"
          />
          <button
            onClick={onSend}
            disabled={isLoading || !userInput.trim()}
            className="absolute right-2 top-2 p-3 bg-glow-gradient rounded-xl text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-20 flex items-center gap-2 group shadow-[0_0_15px_rgba(0,245,212,0.2)]"
          >
            <span className="text-[10px] uppercase font-bold hidden group-hover:block ml-1">Send</span>
            <IconSend />
          </button>
        </div>
      </div>
    </main>
  );
};

export default ChatBox;
