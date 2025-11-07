# The Opponent Framework

> *"The best ideas survive opposition; the rest get refined."*

A three-stage AI-powered system that helps create structured notes using the [Noma method](https://www.youtube.com/watch?v=SAsZDg2l1R0), automatically links them within your Obsidian second brain, and then challenges your arguments using an adversarial AI agent. Built to combat echo chambers by providing systematic opposition to your ideas using relevant sources from your own knowledge base.

The full story on the origin/logic behind the framework can be found in my [simple and elegant website](https://simple-elegant-web.site/projects/the_opponent_framework). It has cool drawings.

**Current Version**: REST API interface
**Next Version**: Telegram bot integration (coming soon)

## How It Works

The Opponent Framework operates in three stages:

1. **Structured Note Creation**: Uses the Noma method with AI assistance to create well-formed notes from your 5 reflections (what's interesting, what it reminds you of, similarities, differences, and importance)

2. **Intelligent Linking**: Automatically finds connections between your new note and existing notes in your Obsidian vault using RAG (Retrieval-Augmented Generation) with semantic search

3. **Adversarial Opposition**: An AI agent retrieves counter-evidence from your knowledge base, analyzes your claim for weaknesses, and challenges your arguments using only evidence from your own notes - no subjective opinions

## Tech Stack

**Backend (Python):**
- **LangGraph/LangChain**: Orchestrates the three-stage pipeline and manages agent workflows
- **ChromaDB**: Vector database for RAG operations on markdown files
- **Ollama**: Local open-source LLM inference (privacy-first, no API costs)
- **FastAPI**: REST API for client communication. Also, was made by a Colombian!
- **uv**: Fast Python package management and virtual environment handling

**Infrastructure:**
- **Docker Compose**: Single-command deployment of backend services
- **Multi-stage Docker builds**: Optimized images for production

**Coming in Next Version:**
- **python-telegram-bot**: Direct Telegram bot integration (more secure than webhook approach)
- **Telegram Bot Interface**: Native bot commands for note creation, linking, and opponent interactions

### Key Design Decisions

- **Local LLM with Ollama**: Privacy-focused, no external API dependencies, zero inference costs. Tradeoff: requires decent hardware (GPU recommended)
- **ChromaDB for RAG**: Lightweight, embedded vector database with good Python integration. Alternative to heavier solutions like Pinecone or Weaviate
- **LangGraph over raw LangChain**: Better state management for multi-stage workflows with conditional branching
- **uv over pip/poetry**: 10-100x faster package resolution and installation
- **REST API First**: Clean API design allows for flexible client implementations (CLI, web UI, or future Telegram bot)

## Installation

### Prerequisites

- **Python 3.11+** (for backend)
- **Docker & Docker Compose** (recommended for easy deployment)
- **Ollama** installed locally or accessible via network
- **uv** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Option 1: Docker Compose (Recommended)

1. Clone the repository and configure environment:
```bash
cd the_opponent_framework
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

**Important Docker Configuration:**
- `VAULT_PATH_HOST`: Absolute path to your Obsidian vault on your host machine (e.g., `/home/user/Documents/obsidian`)
- `OLLAMA_BASE_URL`:
  - **Mac/Windows (Docker Desktop)**: Use `http://host.docker.internal:11434` (default)
  - **Linux**: Use `http://172.17.0.1:11434` or your host IP
- The container will mount your vault as read-only to `/obsidian` inside the container

2. Ensure Ollama is running on your host and has the desired model:
```bash
ollama pull llama3.1  # or your preferred model
ollama serve  # Make sure Ollama is running
```

3. Start the backend service:
```bash
docker-compose up --build
```

The backend API will be available at http://localhost:8000

**For Linux users**: If the default Ollama URL doesn't work, find your Docker bridge IP:
```bash
ip addr show docker0 | grep inet
# Use the IP address in OLLAMA_BASE_URL
```

### Option 2: Manual Setup (Development)

**Backend:**
```bash
cd backend
uv venv
source .venv/bin/activate 
uv pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your configuration
```

**Run development server:**
```bash
cd backend
uv run uvicorn opponent.main:app --reload --host 0.0.0.0 --port 8000
```

### Setting Up Your Telegram Bot (Coming in Next Version)

The Telegram bot integration will be available in the next release. For now, interact with the API directly using HTTP clients, cURL, or build your own client interface.

## Configuration

Create `backend/.env` with the following variables:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# ChromaDB Configuration
CHROMA_PERSIST_DIR=./data/chroma
CHROMA_COLLECTION=obsidian_notes

# Obsidian Vault Path
VAULT_PATH=/path/to/your/obsidian/vault

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Vector Search Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

## Usage

Interact with the Opponent Framework through the REST API. Once the backend is running, you can use any HTTP client (cURL, Postman, HTTPie, or build your own client) to interact with the endpoints:

### 1. Note Creation (Noma Method)

Send a POST request with the 5 Noma reflections to create a structured note:
- Provide your 5 reflections: what's interesting, what it reminds you of, why it's similar, why it's different, why it's important
- AI synthesizes your reflections into a coherent note with title, tags, and markdown
- Returns the complete note ready to save to your Obsidian vault

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/notes/create \
  -H "Content-Type: application/json" \
  -d '{
    "interesting": "I find it fascinating how distributed systems handle consensus...",
    "reminds_me": "This reminds me of how communities make decisions without central authority...",
    "similar_because": "Both require agreement between independent parties without a leader...",
    "different_because": "Computer systems can verify truth mathematically, humans cannot...",
    "important_because": "Understanding this helps design better collaborative tools...",
    "has_internet": false
  }'
```

### 2. Note Linking

Find related notes to link:
- System uses RAG to find semantically similar notes in your vault
- Returns suggested links with relevance scores and reasons
- You can then manually add the links to your note

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/links/find \
  -H "Content-Type: application/json" \
  -d '{
    "note_path": "vault/my_note.md",
    "note_content": "Your note content here...",
    "max_links": 5
  }'
```

### 3. The Opponent

Challenge a claim with evidence-based opposition:
- Provide a note or claim to challenge
- The agent retrieves counter-evidence from your knowledge base
- Returns detailed analysis with logical challenges
- Uses only evidence from your vault - no subjective opinions

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/opponent/challenge \
  -H "Content-Type: application/json" \
  -d '{
    "note_content": "Your claim or argument here...",
    "note_path": "vault/optional_note.md",
    "context": "Optional additional context...",
    "max_evidence": 5
  }'
```

### 4. Vault Management

Index your Obsidian vault for RAG operations:
- Scans all markdown files in your vault
- Creates embeddings and stores in ChromaDB
- Required before using linking or opponent features

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/vault/index \
  -H "Content-Type: application/json" \
  -d '{"vault_path": "/path/to/your/obsidian/vault"}'
```

## API Endpoints

The backend exposes a REST API for any clients you want to build (CLI tools, web interfaces, mobile apps, or the future Telegram bot):

### Note Creation
- `POST /api/notes/create` - Create a new note using Noma method
  - Body: `{ "interesting": "...", "reminds_me": "...", "similar_because": "...", "different_because": "...", "important_because": "...", "has_internet": false }`
  - Returns: `{ "title": "...", "tags": [...], "content": "...", "markdown": "...", "filename": "..." }`

- `GET /api/notes/health` - Check note creation service health

### Note Linking
- `POST /api/links/find` - Find potential links for a note
  - Body: `{ "note_path": "...", "note_content": "...", "max_links": 5 }`
  - Returns: `{ "note_path": "...", "suggested_links": [...], "summary": "...", "count": 0 }`

- `GET /api/links/health` - Check note linking service health

### Opponent
- `POST /api/opponent/challenge` - Challenge a claim with evidence-based opposition
  - Body: `{ "note_content": "...", "note_path": "..." (optional), "context": "..." (optional), "max_evidence": 5 }`
  - Returns: `{ "summary": "...", "detailed_analysis": "...", "counter_evidence": [...], "evidence_count": 0 }`

- `GET /api/opponent/health` - Check opponent service health

### Vault Management
- `POST /api/vault/index` - Index a vault directory into ChromaDB
  - Body: `{ "vault_path": "/path/to/vault" }`
  - Returns: `{ "total_notes": 0, "total_chunks": 0, "vault_path": "..." }`

- `GET /api/vault/health` - Check vault service health

### General
- `GET /` - API information and available endpoints
- `GET /health` - Global health check endpoint
- `GET /docs` - Interactive API documentation (Swagger UI)

## Development

### Adding Custom Prompts

Edit `backend/src/opponent/prompts/opponent_prompts.py` to customize the note creation process and opponent behavior. The framework is designed to be flexible with your specific Noma method implementation.


## Customization

### Using Different LLM Models

Change the `OLLAMA_MODEL` in `.env` to any Ollama-supported model:
- `phi3:3.8b` - Smaller, good for low-resource setups (like my laptop)
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
- Check `CHROMA_PERSIST_DIR` has write permissions
- Clear and rebuild: delete the directory and restart

**API connection issues:**
- Verify the backend service is running on the expected port
- Check firewall rules if connecting remotely
- Review logs for any startup errors
- Test with a simple curl command to `/health` endpoint

**Obsidian vault access:**
- Verify `VAULT_PATH` is correct and accessible
- Check file permissions for read/write access

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! This project is designed to be extensible:
- Add new note creation methods
- Improve linking algorithms
- Enhance opponent reasoning strategies
- Add new data sources beyond Obsidian
- Build client interfaces (CLI, web UI, mobile apps)
- Help implement the Telegram bot integration (coming soon!)

---

**Remember**: The opponent isn't here to attack you - it's here to make your thinking stronger by exposing it to systematic challenge. The best ideas survive opposition; the rest get refined.
