# The Opponent Framework Backend

Well... most of the explanation is in the main README.md file at the root of the repository. But because for some reason that I was way to lazy to understand, `uv` asks for a README.md file in this folder, so... here is a quick overview of the backend architecture, styled by the ~not~ always reliable Claude:

```mermaid
graph TB
    subgraph "API Layer - FastAPI"
        API[/"FastAPI Server<br/>(main.py)"\]
        NE["/api/notes/*"]
        LE["/api/links/*"]
        OE["/api/opponent/*"]
        VE["/api/vault/*"]
    end

    subgraph "Agent Layer"
        NCA["NoMa Note Creator<br/>(noma_note_creator.py)"]
        NLA["Note Linker<br/>(note_linker.py)"]
        OA["Opponent Agent<br/>(opponent_agent.py)"]
    end

    subgraph "RAG Layer"
        VS["VectorStore<br/>(vectorstore.py)"]
        RET["Retriever<br/>(retrieval.py)"]
        CB[("ChromaDB<br/>Vector Store")]
    end

    subgraph "LLM Layer"
        OL["Ollama Server<br/>(External)"]
    end

    subgraph "Data Layer"
        VAULT[("Obsidian Vault<br/>Markdown Files")]
    end

    %% Client to API
    CLIENT([HTTP Clients]) --> API

    %% API to Endpoints
    API --> NE
    API --> LE
    API --> OE
    API --> VE

    %% Endpoints to Agents
    NE --> NCA
    LE --> NLA
    OE --> OA
    VE --> VS

    %% Agents to LLM
    NCA --> OL
    NLA --> OL
    OA --> OL

    %% Agents to RAG
    NLA --> RET
    OA --> RET

    %% RAG internals
    RET --> VS
    RET --> OL
    VS <--> CB

    %% Data access
    VS --> VAULT
    CB -.embeddings.-> VAULT
    NCA -.save note.-> VAULT

    %% Styling
    classDef api fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef agent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef rag fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef llm fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    classDef data fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef client fill:#e1f5ff,stroke:#01579b,stroke-width:2px

    class CLIENT client
    class API,NE,LE,OE,VE api
    class NCA,NLA,OA agent
    class VS,RET,CB rag
    class OL llm
    class VAULT data
```
