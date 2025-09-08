# RAG Server API Endpoints Documentation

## Consistent API Structure (Updated: 2025-09-09)

All main service endpoints now use `/api` prefix for consistency and better organization.

## Endpoint Structure

### 🏥 Health Endpoints
- `GET /health` - Basic health check (no prefix for simplicity)
- `GET /api/health/detailed` - Detailed health information

### 📝 Core Service Endpoints (/api prefix)
- `POST /api/ask` - Process questions through RAG pipeline
- `POST /api/ingest` - Ingest documents into the system
- `GET /api/ask/status` - Get ask service status
- `GET /api/ingest/status` - Get ingest service status

### 📊 RAG Management (/api/rag prefix)
- `GET /api/rag/stats` - Get vector store statistics
- `GET /api/rag/collections` - List collections

### 📁 Namespace Management (/api prefix)
- `GET /api/namespaces` - List all namespaces
- `POST /api/switch_namespace` - Switch to different namespace
- `DELETE /api/namespaces/{name}` - Delete a namespace

### ⚙️ Configuration Management (/api/config prefix)
- `GET /api/config/reload` - Reload configuration
- `GET /api/config/current` - Get current configuration
- `POST /api/config/update` - Update configuration
- `GET /api/config/section/{section}` - Get specific config section

### 🔧 Chunker Management (/api/chunkers prefix)
- `GET /api/chunkers/strategies` - List available strategies
- `GET /api/chunkers/strategy` - Get current strategy
- `POST /api/chunkers/strategy` - Set strategy
- `GET /api/chunkers/params` - Get current parameters
- `POST /api/chunkers/params` - Set parameters
- `POST /api/chunkers/analyze` - Analyze text
- `POST /api/chunkers/preview` - Preview chunking
- `GET /api/chunkers/health` - Chunker health check

## Client Updates Required

The Qt client (qt_app.py) and UI components have been updated to use the `/api` prefix:

### Updated Client Calls:
```python
# Before (inconsistent)
/ask                    → /api/ask
/ingest                 → /api/ingest
/config/reload          → /api/config/reload

# After (consistent)
/api/ask                ✅
/api/ingest             ✅
/api/config/reload      ✅
/api/rag/stats          ✅ (unchanged)
/api/chunkers/strategy  ✅ (unchanged)
```

## Testing

Run the consistency test to verify all endpoints:
```bash
python tests/test_api_consistency.py
```

## Benefits of Consistent API Structure

1. **Clarity**: All API endpoints are clearly distinguished with `/api` prefix
2. **Organization**: Related endpoints are grouped under sub-prefixes
3. **Security**: Easy to apply middleware/authentication to all `/api/*` routes
4. **Documentation**: Clear API structure for external consumers
5. **Versioning**: Easy to add versioning later (e.g., `/api/v2/`)

## Migration Notes

- All clients have been updated to use `/api` prefix
- Server routers consistently use APIRouter with appropriate prefixes
- No breaking changes for health endpoint (`/health` remains without prefix)
