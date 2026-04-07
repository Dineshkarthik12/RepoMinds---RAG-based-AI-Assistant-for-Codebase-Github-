"""
RepoMinds — GitHub Repository RAG System
A Streamlit app that analyzes GitHub repositories and answers
developer queries using FAISS vector search + Gemini LLM.
"""

import os
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="RepoMinds",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* ── Import fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0B0E14;
}

/* ── Header gradient (Teal to Cyan) ── */
.main-header {
    background: linear-gradient(135deg, #00F5D4 0%, #00D2FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 700;
    text-align: center;
    padding: 0.5rem 0;
    letter-spacing: -1px;
    font-family: 'JetBrains Mono', monospace;
}

.sub-header {
    text-align: center;
    color: #94A3B8;
    font-size: 1.05rem;
    margin-top: -0.5rem;
    margin-bottom: 2rem;
    font-weight: 300;
}

/* ── Glass card (Darker with Teal border) ── */
.glass-card {
    background: rgba(17, 25, 40, 0.75);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(0, 245, 212, 0.2);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(0, 245, 212, 0.5);
    box-shadow: 0 0 20px rgba(0, 245, 212, 0.1);
}

/* ── Stat pills (Teal theme) ── */
.stat-row {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin: 1rem 0;
}
.stat-pill {
    background: linear-gradient(135deg, rgba(0,245,212,0.1), rgba(0,210,255,0.05));
    border: 1px solid rgba(0, 245, 212, 0.2);
    border-radius: 12px;
    padding: 0.75rem 1.25rem;
    flex: 1;
    min-width: 140px;
    text-align: center;
}
.stat-pill .stat-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #00F5D4;
}
.stat-pill .stat-label {
    font-size: 0.78rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 2px;
}

/* ── Source chip (Teal theme) ── */
.source-chip {
    display: inline-block;
    background: rgba(0, 245, 212, 0.1);
    border: 1px solid rgba(0, 245, 212, 0.3);
    border-radius: 8px;
    padding: 0.25rem 0.75rem;
    margin: 0.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: #00F5D4;
}

/* ── Sidebar styling ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B0E14 0%, #111827 100%);
    border-right: 1px solid rgba(0, 245, 212, 0.1);
}

/* ── Buttons (Teal gradient) ── */
.stButton > button {
    background: linear-gradient(135deg, #00F5D4, #00D2FF) !important;
    color: #0B0E14 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    width: 100%;
}
.stButton > button:hover {
    box-shadow: 0 4px 20px rgba(0, 245, 212, 0.4) !important;
    transform: translateY(-1px);
}

/* ── Text input ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(17, 25, 40, 0.8) !important;
    border: 1px solid rgba(0, 245, 212, 0.2) !important;
    border-radius: 12px !important;
    color: #FAFAFA !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #00F5D4 !important;
    box-shadow: 0 0 0 2px rgba(0, 245, 212, 0.2) !important;
}

/* ── Chat messages ── */
.answer-block {
    background: rgba(17, 25, 40, 0.5);
    border-left: 3px solid #00F5D4;
    border-radius: 0 12px 12px 0;
    padding: 1.25rem;
    margin: 1rem 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0, 245, 212, 0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 245, 212, 0.5); }
</style>
""", unsafe_allow_html=True)


# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown('<h1 class="main-header">🧠 RepoMinds</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Analyze any GitHub repository with AI — ask questions about code structure, functions, and architecture</p>',
    unsafe_allow_html=True,
)

# ─── Initialize session state ────────────────────────────────────────────────

if "ingested" not in st.session_state:
    st.session_state.ingested = False
if "stats" not in st.session_state:
    st.session_state.stats = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ─── Sidebar — Repository Ingestion ─────────────────────────────────────────

with st.sidebar:
    st.markdown("### 📂 Repository")
    repo_url = st.text_input(
        "GitHub URL",
        placeholder="https://github.com/user/repo",
        label_visibility="collapsed",
    )

    if st.button("🚀 Ingest Repository", use_container_width=True):
        if not repo_url or not repo_url.startswith("http"):
            st.error("Please enter a valid GitHub URL.")
        else:
            with st.status("Ingesting repository…", expanded=True) as status:
                try:
                    import requests
                    import json

                    stage_labels = {
                        "fetch_metadata": "📡 Fetching Metadata",
                        "extract": "📥 Downloading Files",
                        "embed": "🧠 Embedding code",
                        "index": "📦 Building Index",
                        "done": "✅ Complete",
                    }

                    backend_url = os.getenv("API_URL", "http://localhost:8000")
                    response = requests.post(f"{backend_url}/ingest", json={"repo_url": repo_url}, stream=True)
                    if response.status_code != 200:
                        raise Exception(f"Backend error: {response.text}")

                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line)
                            if data.get("type") == "error":
                                raise Exception(data.get("detail"))
                            elif data.get("type") == "progress":
                                stage = data.get("stage")
                                detail = data.get("detail")
                                label = stage_labels.get(stage, stage)
                                st.write(f"{label}: {detail}")
                            elif data.get("type") == "result":
                                st.session_state.ingested = True
                                st.session_state.stats = data.get("stats")
                                st.session_state.chat_history = []
                                status.update(label="✅ Repository ingested!", state="complete")

                except Exception as e:
                    status.update(label="❌ Ingestion failed", state="error")
                    st.error(str(e))

    # ── Stats display ──
    if st.session_state.ingested:
        stats = st.session_state.stats
        st.markdown("---")
        st.markdown("### 📊 Index Stats")
        st.markdown(f"""
        <div class="glass-card">
            <div class="stat-row">
                <div class="stat-pill">
                    <div class="stat-value">{stats.get('num_files', 0)}</div>
                    <div class="stat-label">Files</div>
                </div>
                <div class="stat-pill">
                    <div class="stat-value">{stats.get('num_chunks', 0)}</div>
                    <div class="stat-label">Chunks</div>
                </div>
            </div>
            <div class="stat-row">
                <div class="stat-pill">
                    <div class="stat-value">{stats.get('index_size', 0)}</div>
                    <div class="stat-label">Vectors</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Settings ──
    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    top_k = st.slider("Chunks to retrieve (k)", min_value=1, max_value=20, value=5)

    st.markdown("---")
    st.markdown(
        '<p style="text-align:center;color:#64748B;font-size:0.75rem;">'
        'Built with FAISS • Sentence-Transformers • Gemini</p>',
        unsafe_allow_html=True,
    )


# ─── Main area — Q&A Interface ──────────────────────────────────────────────

if not st.session_state.ingested:
    # Landing state
    st.markdown("""
    <div class="glass-card" style="text-align:center;padding:3rem 2rem;">
        <p style="font-size:3rem;margin-bottom:0.5rem;">📡</p>
        <p style="font-size:1.2rem;color:#C4B5FD;font-weight:500;">
            No repository loaded yet
        </p>
        <p style="color:#94A3B8;font-size:0.95rem;">
            Paste a GitHub URL in the sidebar and click <strong>Ingest Repository</strong> to get started.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <p style="font-size:2rem;">🔍</p>
            <p style="color:#C4B5FD;font-weight:600;">Semantic Search</p>
            <p style="color:#94A3B8;font-size:0.85rem;">
                Find relevant code using meaning, not just keywords
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <p style="font-size:2rem;">🧠</p>
            <p style="color:#C4B5FD;font-weight:600;">AI Explanations</p>
            <p style="color:#94A3B8;font-size:0.85rem;">
                Get clear, context-grounded answers from Gemini
            </p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="glass-card" style="text-align:center;">
            <p style="font-size:2rem;">⚡</p>
            <p style="color:#C4B5FD;font-weight:600;">Fast Retrieval</p>
            <p style="color:#94A3B8;font-size:0.85rem;">
                FAISS-powered vector search over thousands of chunks
            </p>
        </div>
        """, unsafe_allow_html=True)

else:
    # ── Chat interface ──
    repo_name = st.session_state.stats.get("repo_name", "repo")
    st.markdown(
        f'<div style="margin-bottom:1rem;">'
        f'<span class="source-chip">📂 {repo_name}</span> loaded and ready for questions'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Render chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🧠"):
                st.markdown(msg["answer"])
                if msg.get("sources"):
                    with st.expander("📎 View source snippets", expanded=False):
                        for src in msg["sources"]:
                            st.markdown(
                                f'<span class="source-chip">{src["file_path"]} '
                                f'(L{src["start_line"]}–{src["end_line"]})</span>',
                                unsafe_allow_html=True,
                            )
                            st.code(src["text"], language=src.get("language", ""))

    # ── Input ──
    user_question = st.chat_input(f"Ask about {repo_name}…")

    if user_question:
        # Show user message immediately
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question,
        })
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_question)

        # Generate answer
        with st.chat_message("assistant", avatar="🧠"):
            with st.spinner("Thinking…"):
                try:
                    import requests
                    backend_url = os.getenv("API_URL", "http://localhost:8000")
                    response = requests.post(f"{backend_url}/query", json={"question": user_question, "k": top_k})
                    if response.status_code != 200:
                        raise Exception(f"Backend error: {response.json().get('detail', response.text)}")
                    result = response.json()

                    st.markdown(result["answer"])

                    if result.get("sources"):
                        with st.expander("📎 View source snippets", expanded=False):
                            for src in result["sources"]:
                                st.markdown(
                                    f'<span class="source-chip">{src["file_path"]} '
                                    f'(L{src["start_line"]}–{src["end_line"]})</span>',
                                    unsafe_allow_html=True,
                                )
                                st.code(src["text"], language=src.get("language", ""))

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "answer": result["answer"],
                        "sources": result.get("sources", []),
                    })

                except Exception as e:
                    st.error(f"Error: {str(e)}")
