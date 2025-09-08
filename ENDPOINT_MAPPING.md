# RAG Server Endpoint Mapping

## Updated Endpoint Structure (2025-09-09)

### Core Endpoints (No Prefix)
These endpoints are directly accessible without /api prefix to maintain backward compatibility with existing clients:

- `POST /ask` - Process questions through RAG pipeline
- `POST /ingest` - Ingest documents into the system
- `GET /ask/status` - Get ask service status
- `GET /ingest/status` - Get ingest service status

### Health Endpoints
- `GET /health` - Basic health check
- `GET /api/health/detailed` - Detailed health information

### RAG Management Endpoints (/api/rag prefix)
- `GET /api/rag/stats` - Get vector store statistics
- `GET /api/rag/collections` - List collections

### Namespace Management (/api prefix)
- `GET /api/namespaces` - List all namespaces
- `POST /api/switch_namespace` - Switch to different namespace
- `DELETE /api/namespaces/{name}` - Delete a namespace

### Configuration Management (/api/config prefix)
- `GET /api/config/reload` - Reload configuration
- `GET /api/config/current` - Get current configuration
- `POST /api/config/update` - Update configuration
- `GET /api/config/section/{section}` - Get specific config section

### Chunker Management (/api/chunkers prefix)
- `GET /api/chunkers/strategies` - List available strategies
- `GET /api/chunkers/strategy` - Get current strategy
- `POST /api/chunkers/strategy` - Set strategy
- `GET /api/chunkers/params` - Get current parameters
- `POST /api/chunkers/params` - Set parameters
- `POST /api/chunkers/analyze` - Analyze text
- `POST /api/chunkers/preview` - Preview chunking
- `GET /api/chunkers/health` - Chunker health check

## Client-Server Compatibility

### Qt Client (qt_app.py) calls:
- `/ask` ✅ (compatible)
- `/ingest` ✅ (compatible)
- `/api/rag/stats` ✅ (compatible)
- `/api/chunkers/strategy` ✅ (compatible)
- `/config/reload` ❌ (needs update to `/api/config/reload`)

### Changes Made:
1. Removed `/api` prefix from `ask` and `ingest` routers for backward compatibility
2. Kept `/api` prefix for other routers as they are already expected with prefix
3. All Pydantic models updated with `protected_namespaces = ()` to avoid warnings

## Testing

Run the updated integration test:
```bash
python tests/test_integration_updated.py
```

## Notes
- The server now supports both old and new client versions
- No client code changes required for basic functionality
- Future clients should use the documented endpoints above
