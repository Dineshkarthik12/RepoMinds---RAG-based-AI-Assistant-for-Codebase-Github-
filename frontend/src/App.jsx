import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatBox from './components/ChatBox';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [repoUrl, setRepoUrl] = useState('');
  const [ingestionStatus, setIngestionStatus] = useState('idle');
  const [stats, setStats] = useState({ progress: null, repo_name: null, num_files: 0, num_chunks: 0 });
  const [chatHistory, setChatHistory] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // 1. Handle Repository Ingestion (Streaming NDJSON)
  const handleIngest = async () => {
    if (!repoUrl) return;
    setIngestionStatus('loading');
    setStats({ progress: null, repo_name: null, num_files: 0, num_chunks: 0 });
    
    try {
      const response = await fetch(`${API_BASE_URL}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (!line.trim()) continue;
          const data = JSON.parse(line);
          if (data.type === 'progress') setStats(p => ({ ...p, progress: data }));
          if (data.type === 'result') {
            setStats(p => ({ ...p, ...data.stats, progress: { stage: 'done', detail: 'Complete!' } }));
            setIngestionStatus('done');
          }
        }
      }
    } catch (e) {
      setIngestionStatus('error');
    }
  };

  // 2. Handle Query Submission (Streaming NDJSON)
  const handleSend = async () => {
    if (!userInput.trim() || isLoading) return;

    const userMsg = { role: 'user', content: userInput };
    setChatHistory(prev => [...prev, userMsg]);
    setIsLoading(true);
    const questionText = userInput;
    setUserInput('');

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: questionText, k: 5 }),
      });

      if (!response.ok) throw new Error('Query failed');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      // Initialize a new assistant message in the history
      let assistantMsg = { role: 'assistant', answer: '', sources: [] };
      setChatHistory(prev => [...prev, assistantMsg]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'sources') {
              assistantMsg.sources = data.sources;
              // Update state with sources
              setChatHistory(prev => {
                const newHistory = [...prev];
                newHistory[newHistory.length - 1] = { ...assistantMsg };
                return newHistory;
              });
            } else if (data.type === 'token') {
              assistantMsg.answer += data.token;
              // Update state with new token
              setChatHistory(prev => {
                const newHistory = [...prev];
                newHistory[newHistory.length - 1] = { ...assistantMsg };
                return newHistory;
              });
            } else if (data.type === 'error') {
              throw new Error(data.detail);
            }
          } catch (e) {
            console.error('Error parsing query stream:', e);
          }
        }
      }
    } catch (err) {
      console.error(err);
      setChatHistory(prev => [
        ...prev, 
        { role: 'assistant', answer: `❌ Error: ${err.message}`, sources: [] }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', backgroundColor: '#0B0E14', color: 'white', fontFamily: 'sans-serif', overflow: 'hidden' }}>
      <Sidebar 
        repoUrl={repoUrl} 
        setRepoUrl={setRepoUrl} 
        onIngest={handleIngest} 
        ingestionStatus={ingestionStatus}
        stats={stats}
      />
      <div style={{ flex: 1, height: '100%', overflow: 'hidden' }}>
        <ChatBox 
          chatHistory={chatHistory}
          userInput={userInput}
          setUserInput={setUserInput}
          onSend={handleSend}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}

export default App;
