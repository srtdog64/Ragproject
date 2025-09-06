# Chunking API Documentation

## Base URL
```
http://localhost:7001/api/chunkers
```

## Endpoints

### 1. Strategy Management

#### GET /strategies
List all available chunking strategies
```bash
curl http://localhost:7001/api/chunkers/strategies
```

Response:
```json
{
  "strategies": [
    {
      "name": "adaptive",
      "description": "Automatically selects the best strategy...",
      "active": true
    },
    {
      "name": "sentence",
      "description": "Splits text at sentence boundaries...",
      "active": false
    }
  ],
  "current": "adaptive"
}
```

#### GET /strategy
Get current active strategy and its parameters
```bash
curl http://localhost:7001/api/chunkers/strategy
```

Response:
```json
{
  "strategy": "adaptive",
  "params": {
    "maxTokens": 512,
    "windowSize": 1200,
    "overlap": 200,
    "semanticThreshold": 0.82,
    "language": "ko",
    "sentenceMinLen": 10,
    "paragraphMinLen": 50
  }
}
```

#### POST /strategy
Set the active chunking strategy
```bash
curl -X POST http://localhost:7001/api/chunkers/strategy \
  -H "Content-Type: application/json" \
  -d '{"strategy": "sentence"}'
```

Response:
```json
{
  "message": "Strategy set to sentence",
  "strategy": "sentence",
  "params": {...}
}
```

### 2. Parameters Management

#### GET /params
Get current chunking parameters
```bash
curl http://localhost:7001/api/chunkers/params
```

Response:
```json
{
  "maxTokens": 512,
  "windowSize": 1200,
  "overlap": 200,
  "semanticThreshold": 0.82,
  "language": "ko",
  "sentenceMinLen": 10,
  "paragraphMinLen": 50
}
```

#### POST /params
Update chunking parameters (partial updates supported)
```bash
curl -X POST http://localhost:7001/api/chunkers/params \
  -H "Content-Type: application/json" \
  -d '{"maxTokens": 1024, "overlap": 100}'
```

Response:
```json
{
  "message": "Parameters updated successfully",
  "params": {
    "maxTokens": 1024,
    "windowSize": 1200,
    "overlap": 100,
    ...
  }
}
```

### 3. Analysis and Preview

#### POST /analyze
Analyze text and get suggested chunking strategy
```bash
curl -X POST http://localhost:7001/api/chunkers/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text to analyze..."}'
```

Response:
```json
{
  "suggested_strategy": "paragraph",
  "text_stats": {
    "length": 2500,
    "lines": 45,
    "words": 380,
    "avg_line_length": 55.5
  }
}
```

#### POST /preview
Preview how text would be chunked with specific strategy
```bash
curl -X POST http://localhost:7001/api/chunkers/preview \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text to chunk...",
    "strategy": "sentence",
    "params": {"maxTokens": 256}
  }'
```

Response:
```json
{
  "strategy": "sentence",
  "chunks": [
    {
      "id": "preview_0",
      "index": 0,
      "text_preview": "First chunk text...",
      "length": 245,
      "meta": {...}
    }
  ],
  "summary": {
    "total_chunks": 5,
    "avg_chunk_size": 240,
    "min_chunk_size": 180,
    "max_chunk_size": 300
  },
  "params": {...}
}
```

### 4. Health Check

#### GET /health
Check if chunking service is operational
```bash
curl http://localhost:7001/api/chunkers/health
```

Response:
```json
{
  "status": "healthy",
  "current_strategy": "adaptive",
  "available_strategies": 5
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Unknown strategy: invalid_strategy. Available: ['sentence', 'paragraph', ...]"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error message describing what went wrong"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service unhealthy: Registry not initialized"
}
```

## Usage Examples

### Python
```python
import requests

# Get current strategy
response = requests.get("http://localhost:7001/api/chunkers/strategy")
data = response.json()
print(f"Current strategy: {data['strategy']}")

# Change strategy
response = requests.post(
    "http://localhost:7001/api/chunkers/strategy",
    json={"strategy": "paragraph"}
)

# Update parameters
response = requests.post(
    "http://localhost:7001/api/chunkers/params",
    json={"maxTokens": 1024, "overlap": 150}
)
```

### JavaScript
```javascript
// Get current strategy
fetch('http://localhost:7001/api/chunkers/strategy')
  .then(res => res.json())
  .then(data => console.log(`Current strategy: ${data.strategy}`));

// Change strategy
fetch('http://localhost:7001/api/chunkers/strategy', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({strategy: 'paragraph'})
});
```

## Best Practices

1. **Always check current strategy before making changes**
   ```python
   current = requests.get(".../strategy").json()
   if current['strategy'] != desired_strategy:
       requests.post(".../strategy", json={"strategy": desired_strategy})
   ```

2. **Use preview before applying to production**
   ```python
   preview = requests.post(".../preview", json={
       "text": sample_text,
       "strategy": new_strategy,
       "params": new_params
   }).json()
   if preview['summary']['total_chunks'] < 100:
       # Apply the strategy
       requests.post(".../strategy", json={"strategy": new_strategy})
   ```

3. **Handle errors gracefully**
   ```python
   try:
       response = requests.post(".../strategy", json={"strategy": "unknown"})
       response.raise_for_status()
   except requests.exceptions.HTTPError as e:
       if response.status_code == 400:
           print(f"Invalid strategy: {response.json()['detail']}")
   ```
