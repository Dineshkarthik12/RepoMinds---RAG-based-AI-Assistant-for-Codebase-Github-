# 🧠 RepoMinds

**Analyze any GitHub repository with AI** — ask natural-language questions about code structure, functions, and architecture and get context-grounded answers.

RepoMinds clones a GitHub repo, chunks its source files, builds a FAISS vector index using Sentence-Transformers embeddings, and answers developer questions through a Gemini-powered LLM via OpenRouter.

---

## ✨ Features

- **Semantic Code Search** — find relevant code by meaning, not just keywords
- **AI-Powered Explanations** — clear, context-grounded answers with file & line references
- **Fast Retrieval** — FAISS-powered vector search over thousands of code chunks
- **Multi-Language Support** — indexes Python, JavaScript, TypeScript, Java, Go, Rust, C/C++, and 30+ more languages
- **Interactive Chat UI** — beautiful Streamlit interface with chat history and source-snippet expansion

---

## 🏗️ Architecture

```
GitHub Repo URL
      │
      ▼
┌─────────────┐     ┌────────────┐     ┌────────────┐
│  repo_loader │────▶│  chunker   │────▶│  embedder  │
│  (clone)     │     │  (split)   │     │  (encode)  │
└─────────────┘     └────────────┘     └─────┬──────┘
                                             │
                                             ▼
                                     ┌──────────────┐
                                     │ vector_store  │
                                     │ (FAISS index) │
                                     └──────┬───────┘
                                            │
           User Question ──▶ embed ──▶ search ──▶ top-k chunks
                                                      │
                                                      ▼
                                               ┌─────────┐
                                               │   LLM   │
                                               │ (Gemini) │
                                               └────┬────┘
                                                    │
                                                    ▼
                                              AI Answer
```

---

## 📁 Project Structure

```
RepoMinds/
├── app.py                  # Streamlit UI entry point
├── src/
│   ├── __init__.py
│   ├── repo_loader.py      # Clone repos & extract code files
│   ├── chunker.py          # Split source code into chunks
│   ├── embedder.py         # Sentence-Transformers embeddings
│   ├── vector_store.py     # FAISS index build / save / search
│   ├── llm.py              # LLM answer generation (OpenRouter)
│   └── pipeline.py         # End-to-end ingest & query orchestration
├── test_components.py      # Smoke tests for pipeline components
├── .streamlit/
│   └── config.toml         # Streamlit theme configuration
├── requirements.txt
├── .env                    # API keys (not committed)
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- A free **OpenRouter** API key → [openrouter.ai](https://openrouter.ai/)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/<your-username>/RepoMinds.git
   cd RepoMinds
   ```

2. **Create a virtual environment**

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   Create a `.env` file in the project root:

   ```env
   OPENROUTER_API_KEY=your-openrouter-api-key
   ```

### Run the App

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## 🔧 Usage

1. Paste a **GitHub repository URL** in the sidebar.
2. Click **🚀 Ingest Repository** — the app clones, chunks, embeds, and indexes the code.
3. Once ingested, ask any question in the chat input (e.g., *"How does authentication work?"*).
4. View the AI answer along with expandable source-code snippets.

---

## ⚙️ Configuration

| Setting | Location | Default |
|---|---|---|
| LLM model | `src/llm.py` | `google/gemini-2.0-flash-001` |
| Embedding model | `src/embedder.py` | `all-MiniLM-L6-v2` (384-dim) |
| Chunks to retrieve | Sidebar slider | 5 |
| FAISS index path | `src/vector_store.py` | `faiss_index/` |

---

## 🧪 Testing

Run the component smoke tests:

```bash
python test_components.py
```

This validates the chunker, embedder, FAISS vector store, and repo-loader imports.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io/) |
| Embeddings | [Sentence-Transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`) |
| Vector Search | [FAISS](https://github.com/facebookresearch/faiss) |
| LLM | [Gemini 2.0 Flash](https://deepmind.google/technologies/gemini/) via [OpenRouter](https://openrouter.ai/) |
| Repo Cloning | [GitPython](https://gitpython.readthedocs.io/) |

---

## 📄 License

This project is open-source. Feel free to use and modify it as you wish.
