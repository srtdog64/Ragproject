# Server Module Structure

server/
├── __init__.py
├── main.py           # FastAPI app creation and configuration
├── dependencies.py   # DI container and component initialization
├── routers/
│   ├── __init__.py
│   ├── health.py    # Health check endpoints
│   ├── rag.py       # RAG related endpoints (/api/rag/*)
│   ├── ingest.py    # Document ingestion endpoints
│   ├── ask.py       # Query/ask endpoints
│   ├── namespaces.py # Namespace management
│   └── rerankers.py  # Reranker configuration
├── models/
│   ├── __init__.py
│   └── schemas.py    # Pydantic models
└── utils/
    ├── __init__.py
    └── logging.py    # Logging configuration
