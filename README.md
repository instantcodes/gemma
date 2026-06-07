# CampusAI — College & Placement Assistant
### Powered by Gemma 3

AI-powered assistant for academic guidance, placement support, resume analysis, interview preparation, and career guidance.

## Quick Start (Frontend Only — No Setup Required)

Simply open `frontend/index.html` in your browser. The app works with sample data and fallback responses.

## Full Setup (With AI Backend)

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.ai) installed

### Step 1: Install Ollama & Gemma 3
```bash
# Install Ollama from https://ollama.ai
# Then pull Gemma 3:
ollama pull gemma3
ollama serve
```

### Step 2: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 3: Run Backend Server
```bash
cd backend
python main.py
```
Server starts at `http://localhost:8000`

### Step 4: Open Frontend
Open `http://localhost:8000` or `frontend/index.html`

## Features
- 💬 **AI Chat** — Natural language Q&A with RAG
- 📄 **Document Q&A** — Upload & query college documents
- 📝 **Resume Analyzer** — AI-powered scoring & feedback
- ✅ **Eligibility Check** — Match students to companies
- 🎯 **Interview Prep** — AI-generated practice questions
- 🧭 **Career Guidance** — Personalized career recommendations
- 👥 **Student Management** — Admin tools
- 🏢 **Company Management** — Track recruitment drives

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Backend | Python FastAPI |
| AI Model | Gemma 3 via Ollama |
| Vector DB | ChromaDB |
| Database | SQLite |
