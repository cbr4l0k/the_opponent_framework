# The Opponent Framework

A three-stage AI-powered system that helps create structured notes using the Noma method, automatically links them within your Obsidian second brain, and then challenges your arguments using an adversarial AI agent. Built to combat echo chambers by providing systematic opposition to your ideas using relevant sources.

## Why This Exists

Modern social media and AI systems create echo chambers that reinforce existing beliefs rather than challenge them. It's increasingly difficult to find people who will genuinely question your assumptions or point out flaws in your reasoning. The Opponent Framework addresses this by:

1. **Structured Note Creation**: Uses the Noma method with AI assistance to create well-formed notes from your initial thoughts
2. **Intelligent Linking**: Automatically finds connections between your new note and existing notes in your Obsidian vault using RAG (Retrieval-Augmented Generation)
3. **Adversarial Opposition**: An AI agent that finds holes in your arguments, questions your assumptions, and challenges your ideas using relevant sources from your own knowledge base

The goal isn't to win arguments but to strengthen thinking by exposing it to systematic opposition.

## Architecture

### Tech Stack

**Backend (Python):**
- **LangGraph/LangChain**: Orchestrates the three-stage pipeline and manages agent workflows
- **ChromaDB**: Vector database for RAG operations on markdown files
- **Ollama**: Local open-source LLM inference (privacy-first, no API costs)
- **FastAPI**: REST API for frontend communication
- **uv**: Fast Python package management and virtual environment handling

**Frontend (TypeScript/Vite):**
- **Vite + React**: Fast development and optimized production builds
- **TailwindCSS**: Utility-first styling
- **WebSocket support**: Real-time streaming of LLM responses

**Infrastructure:**
- **Docker Compose**: Single-command deployment of all services
- **Multi-stage Docker builds**: Optimized images for production

### Key Design Decisions

- **Local LLM with Ollama**: Privacy-focused, no external API dependencies, zero inference costs. Tradeoff: requires decent hardware (GPU recommended)
- **ChromaDB for RAG**: Lightweight, embedded vector database with good Python integration. Alternative to heavier solutions like Pinecone or Weaviate
- **LangGraph over raw LangChain**: Better state management for multi-stage workflows with conditional branching
- **uv over pip/poetry**: 10-100x faster package resolution and installation
- **Monorepo structure**: Backend and frontend in same repository for easier development and deployment

## Project Structure

```
the_opponent_framework/
├── backend/                    # Python backend
│   ├── src/
│   │   └── opponent/
│   │       ├── __init__.py
│   │       ├── main.py        # FastAPI application entry
│   │       ├── api/           # API endpoints
│   │       │   ├── __init__.py
│   │       │   ├── notes.py   # Note creation endpoints
│   │       │   ├── links.py   # Note linking endpoints
│   │       │   └── opponent.py # Opponent chat endpoints
│   │       ├── agents/        # LangGraph agents
│   │       │   ├── __init__.py
│   │       │   ├── noma_note_creator.py
│   │       │   ├── note_linker.py
│   │       │   └── opponent_agent.py
│   │       ├── rag/           # RAG implementation
│   │       │   ├── __init__.py
│   │       │   ├── vectorstore.py
│   │       │   └── retrieval.py
│   │       ├── config/        # Configuration management
│   │       │   ├── __init__.py
│   │       │   └── settings.py
│   │       └── prompts/       # Prompt templates
│   │           ├── __init__.py
│   │           ├── noma_prompts.py
│   │           └── opponent_prompts.py
│   ├── tests/
│   │   └── __init__.py
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
├── frontend/                   # Vite + React frontend
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── NoteCreator.tsx
│   │   │   ├── NoteLinking.tsx
│   │   │   └── OpponentChat.tsx
│   │   ├── services/
│   │   │   └── api.ts         # Backend API client
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── types/
│   │       └── index.ts
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── tailwind.config.js
├── docker-compose.yml          # Orchestrates all services
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

## Installation

### Prerequisites

- **Python 3.11+** (for backend)
- **Node.js 18+** (for frontend)
- **Docker & Docker Compose** (recommended for easy deployment)
- **Ollama** installed locally or accessible via network
- **uv** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **pnpm** (Node package manager): `npm install -g pnpm`

### Option 1: Docker Compose (Recommended)

1. Clone the repository and configure environment:
```bash
cd the_opponent_framework
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

2. Ensure Ollama is running and has the desired model:
```bash
ollama pull llama3.1  # or your preferred model
```

3. Start all services:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Option 2: Manual Setup (Development)

**Backend:**
```bash
cd backend
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your configuration
```

**Frontend:**
```bash
cd frontend
pnpm install
```

**Run development servers:**
```bash
# Terminal 1 - Backend
cd backend
uv run uvicorn opponent.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
pnpm dev
```

## Configuration

Create `backend/.env` with the following variables:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./data/chroma
CHROMA_COLLECTION_NAME=obsidian_notes

# Obsidian Vault Path
OBSIDIAN_VAULT_PATH=/path/to/your/obsidian/vault

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173

# Vector Search Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

## Usage

### 1. Note Creation (Noma Method)

Navigate to the "Create Note" section in the web interface:
- Enter your initial thoughts or ideas
- The AI uses your custom Noma method prompts to structure the note
- Review and edit the generated note
- Save to your Obsidian vault

### 2. Note Linking

After creating a note:
- The system automatically scans your Obsidian vault
- RAG finds semantically similar notes and concepts
- Suggests links and connections
- You can approve or modify suggested links
- Links are added to the markdown file in Obsidian format

### 3. The Opponent

Access the "Opponent" chat interface:
- The agent can either:
  - Retrieve a specific note by name/topic
  - Select a random note tagged with `#opponent`
- The agent reads the note and linked context
- Challenges arguments, finds logical holes, questions assumptions
- Provides opposition using relevant sources from your vault
- No subjective opinions - only evidence-based challenges

## API Endpoints

### Note Creation
- `POST /api/notes/create` - Create a new note using Noma method
  - Body: `{ "initial_thoughts": "your text" }`
  - Returns: Structured note content

### Note Linking
- `POST /api/links/find` - Find potential links for a note
  - Body: `{ "note_content": "...", "note_path": "..." }`
  - Returns: List of suggested links with relevance scores

- `POST /api/links/apply` - Apply selected links to note
  - Body: `{ "note_path": "...", "links": [...] }`
  - Returns: Updated note content

### Opponent Chat
- `POST /api/opponent/chat` - Start or continue opponent conversation
  - Body: `{ "message": "...", "note_id": "..." (optional) }`
  - Returns: Opponent's response with sources

- `GET /api/opponent/random-note` - Get a random #opponent tagged note
  - Returns: Note content and metadata

- `WebSocket /ws/opponent` - Real-time streaming chat

### Health
- `GET /health` - Health check endpoint

## Development

### Pre-commit Hooks

Install pre-commit hooks for code quality:
```bash
pip install pre-commit
pre-commit install
```

This runs automatically on commit:
- **Python**: ruff (linting), black (formatting), mypy (type checking)
- **TypeScript**: eslint (linting), prettier (formatting)

### Running Tests

**Backend:**
```bash
cd backend
uv run pytest
```

**Frontend:**
```bash
cd frontend
pnpm test
```

### Adding Custom Prompts

Edit `backend/src/opponent/prompts/noma_prompts.py` to customize the note creation process. The framework is designed to be flexible with your specific Noma method implementation.

## Deployment

### Docker Production Build

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Standalone Deployment

The application can be deployed on any system with:
- Docker support (easiest)
- Python 3.11+ and Node.js 18+ (manual)
- Ollama accessible via network (can be on same or different machine)

For production:
1. Set `CORS_ORIGINS` to your frontend domain
2. Use a reverse proxy (nginx/traefik) for HTTPS
3. Configure Ollama with adequate resources (8GB+ RAM, GPU recommended)
4. Backup ChromaDB data directory regularly

## Customization

### Using Different LLM Models

Change the `OLLAMA_MODEL` in `.env` to any Ollama-supported model:
- `llama3.1` - Balanced performance and quality
- `mistral` - Faster, good for quick iterations
- `mixtral` - Better reasoning for complex arguments
- `codellama` - If working with code-heavy notes

### RAG Configuration

Adjust vector search parameters in `.env`:
- `CHUNK_SIZE`: Larger chunks = more context, slower retrieval
- `TOP_K_RESULTS`: More results = better context, slower processing
- Balance based on your vault size and hardware

## Troubleshooting

**Ollama connection issues:**
- Verify Ollama is running: `ollama list`
- Check `OLLAMA_BASE_URL` matches your Ollama instance
- If using Docker, ensure network connectivity

**ChromaDB errors:**
- Check `CHROMA_PERSIST_DIRECTORY` has write permissions
- Clear and rebuild: delete the directory and restart

**Frontend can't connect to backend:**
- Verify `CORS_ORIGINS` includes your frontend URL
- Check both services are running
- Inspect browser console for specific errors

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! This project is designed to be extensible:
- Add new note creation methods
- Improve linking algorithms
- Enhance opponent reasoning strategies
- Add new data sources beyond Obsidian

---

**Remember**: The opponent isn't here to attack you - it's here to make your thinking stronger by exposing it to systematic challenge. The best ideas survive opposition; the rest get refined.
