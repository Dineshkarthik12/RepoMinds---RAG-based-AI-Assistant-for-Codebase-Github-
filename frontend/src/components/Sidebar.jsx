import React from 'react';

// ── Icons (Custom SVGs to avoid crashing lucide-react) ──
const IconDatabase = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>
);
const IconGithub = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
);
const IconRefresh = ({ animate }) => (
  <svg className={animate ? "animate-spin" : ""} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
);
const IconCheck = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
);

const Sidebar = ({ repoUrl, setRepoUrl, onIngest, ingestionStatus, stats }) => {
  const getStatusIcon = () => {
    if (ingestionStatus === 'error') return <span style={{ color: 'red' }}>⚠️</span>;
    if (ingestionStatus === 'done') return <span className="text-cyber-teal"><IconCheck /></span>;
    return <span className="text-cyber-cyan"><IconRefresh animate={stats?.progress} /></span>;
  };

  const STAGE_LABELS = {
    fetch_metadata: "📡 Fetching Metadata",
    extract: "📥 Downloading Files",
    embed: "🧠 Embedding code",
    index: "📦 Building Index",
    done: "✅ Complete",
  };

  return (
    <aside className="w-80 h-full border-r border-cyber-border bg-cyber-black flex flex-col p-6 z-20 overflow-y-auto">
      <div className="flex items-center gap-3 mb-10">
        <div className="p-2 rounded-lg bg-cyber-teal/10 border border-cyber-teal/20">
          <span className="text-cyber-teal"><IconDatabase /></span>
        </div>
        <h1 className="text-xl font-bold font-mono tracking-tighter text-white">REPO<span className="text-cyber-teal">MINDS</span></h1>
      </div>

      <div className="space-y-6 flex-1">
        <div>
          <label className="text-[10px] uppercase tracking-widest text-gray-500 font-bold mb-3 block">Repository</label>
          <div className="relative">
            <input
              type="text"
              placeholder="https://github.com/user/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full bg-cyber-dark/50 border border-cyber-border rounded-xl py-3 pl-10 pr-4 text-sm focus:outline-none focus:border-cyber-teal/50 transition-all text-gray-200 placeholder:text-gray-600"
            />
            <span className="absolute left-3 top-3.5 text-gray-600"><IconGithub /></span>
          </div>
          <button
            onClick={onIngest}
            className="w-full mt-4 bg-glow-gradient text-white font-bold py-3 rounded-xl shadow-[0_4px_20px_rgba(0,245,212,0.3)] hover:shadow-[0_4px_25px_rgba(0,245,212,0.5)] transition-all active:scale-[0.98] text-[10px] uppercase tracking-widest"
          >
            INGEST REPOSITORY
          </button>
        </div>

        {stats?.progress && (
          <div className="glass-effect p-4 border-cyber-border/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase font-bold text-cyber-teal">{STAGE_LABELS[stats.progress.stage] || stats.progress.stage}</span>
              {getStatusIcon()}
            </div>
            <div className="text-[11px] text-gray-400 mb-2 truncate">{stats.progress.detail}</div>
            <div className="w-full bg-cyber-dark h-1 rounded-full overflow-hidden">
              <div 
                className="bg-cyber-teal h-full transition-all duration-500 ease-out" 
                style={{ width: stats.progress.stage === 'done' ? '100%' : '60%' }} 
              />
            </div>
          </div>
        )}

        {stats?.num_files > 0 && (
          <div className="space-y-4">
            <label className="text-[10px] uppercase tracking-widest text-gray-500 font-bold block">Statistics</label>
            <div className="grid grid-cols-2 gap-3">
              <div className="glass-effect p-3 flex flex-col items-center">
                <span className="text-xl font-bold text-white">{stats.num_files}</span>
                <span className="text-[9px] text-gray-500 uppercase">Files</span>
              </div>
              <div className="glass-effect p-3 flex flex-col items-center">
                <span className="text-xl font-bold text-white">{stats.num_chunks}</span>
                <span className="text-[9px] text-gray-500 uppercase">Chunks</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="pt-6 border-t border-cyber-border text-[10px] text-gray-600 text-center font-mono">
        V2.0.0 — CYBER-TEAL EDITION
      </div>
    </aside>
  );
};

export default Sidebar;
