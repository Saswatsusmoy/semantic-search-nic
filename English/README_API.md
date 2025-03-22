# NIC Code Semantic Search API

This document provides comprehensive documentation for the FastAPI-based REST API powering the NIC (National Industrial Classification) Code Semantic Search application. This API enables intelligent search capabilities for finding relevant industry codes based on natural language descriptions.

## 📋 Table of Contents

- [Getting Started](#-getting-started)
- [API Endpoints](#-api-endpoints)
- [Performance Considerations](#-performance-considerations)
- [Error Handling](#-error-handling)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment Recommendations](#-deployment-recommendations)
- [Security Considerations](#-security-considerations)

## 🚀 Getting Started

### Prerequisites

- Python 3.7+ (Python 3.9+ recommended)
- 4GB+ RAM (8GB+ recommended for production)
- Required Python packages:
  - fastapi
  - uvicorn
  - pydantic
  - faiss-cpu (or faiss-gpu for GPU acceleration)
  - sentence-transformers
  - pandas
  - numpy
  - tqdm

### Installation

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone https://github.com/yourusername/semantic-search-nic.git
cd semantic-search-nic

# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
# Basic start with default settings
python start_api.py

# Start with custom configuration
python start_api.py --host 0.0.0.0 --port 8000 --reload --workers 4 --log-level debug
```

#### Command-line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--host` | IP address to bind the server to | `127.0.0.1` |
| `--port` | Port to bind the server to | `8000` |
| `--reload` | Enable auto-reload on code changes (development) | `False` |
| `--workers` | Number of worker processes | `1` |
| `--log-level` | Logging level (debug, info, warning, error, critical) | `info` |

The API will be available at:

- Interactive Swagger UI documentation: `http://localhost:8000/docs`
- Alternative ReDoc documentation: `http://localhost:8000/redoc`
- Base API URL: `http://localhost:8000/`

## 📚 API Endpoints

### Search Endpoint

**POST** `/search`

Search for NIC codes using semantic similarity based on natural language input.

#### Request Body (JSON)

```json
{
  "query": "software development",
  "result_count": 10,
  "search_mode": "standard",
  "show_metrics": true
}
```

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The search query in natural language |
| `result_count` | integer | No | 10 | Number of results to return (1-100) |
| `search_mode` | string | No | "standard" | Search mode: "standard", "strict", or "relaxed" |
| `show_metrics` | boolean | No | false | Whether to include performance metrics in response |

##### Search Modes

- **standard**: Balanced between precision and recall (default)
- **strict**: Higher precision, requiring closer semantic matches
- **relaxed**: Higher recall, including more potential matches

#### Response

```json
{
  "results": [
    {
      "id": "62011",
      "title": "Computer programming activities",
      "description": "Computer programming activities",
      "section": "J",
      "section_description": "Information and communication",
      "division": "62",
      "division_description": "Computer programming, consultancy and related activities",
      "group": "620",
      "group_description": "Computer programming, consultancy and related activities",
      "class": "6201",
      "class_description": "Computer programming activities",
      "subclass": "62011",
      "subclass_description": "Computer programming activities",
      "similarity": 0.879,
      "similarity_percent": 87.9
    },
    // Additional results...
  ],
  "count": 10,
  "metrics": {
    "total_time_ms": 152.45,
    "embedding_time_ms": 103.12,
    "index_time_ms": 22.75,
    "results_count": 20
  }
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `results` | array | List of matching NIC codes with metadata |
| `count` | integer | Number of results returned |
| `metrics` | object | Performance metrics (only if requested) |

Each result contains:

- NIC code hierarchy (section → division → group → class → subclass)
- Descriptions for each level
- Similarity score (0-1 where 1 is exact match)
- Similarity percentage (0-100%)

#### Example Request

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
           "query": "mobile app development for smartphones", 
           "result_count": 5, 
           "search_mode": "standard", 
           "show_metrics": true
         }'
```

### Admin Endpoints

#### Rebuild Index

**POST** `/rebuild-index`

Rebuilds the FAISS vector index from scratch.

##### Request

No parameters required.

##### Response

```json
{
  "status": "success",
  "message": "Index rebuilt successfully",
  "time_taken": 3.45,
  "index_stats": {
    "vector_count": 23456,
    "dimension": 384,
    "index_type": "Flat Inner Product (Cosine Similarity)"
  }
}
```

##### Example Request

```bash
curl -X POST "http://localhost:8000/rebuild-index" -H "Content-Type: application/json"
```

#### Get Index Statistics

**GET** `/get-index-stats`

Returns detailed information about the current state of the FAISS index.

##### Response

```json
{
  "vector_count": 23456,
  "index_type": "Flat Inner Product (Cosine Similarity)",
  "dimension": 384,
  "index_file_exists": true,
  "index_file_path": "/path/to/faiss_index.bin",
  "index_file_size_mb": 35.7,
  "id_map_file_exists": true,
  "id_map_size": 23456,
  "embedding_cache_size": 120,
  "embedding_cache_hit_rate": "85.5%",
  "embedding_requests": 250,
  "last_rebuild": "2023-07-15T14:30:22",
  "memory_usage_mb": 256.3
}
```

##### Example Request

```bash
curl -X GET "http://localhost:8000/get-index-stats" -H "Accept: application/json"
```

#### Clear Embedding Cache

**POST** `/clear-embedding-cache`

Clears the in-memory and disk cache of text embeddings.

##### Response

```json
{
  "status": "success",
  "message": "Embedding cache cleared successfully",
  "cache_stats": {
    "items_cleared": 120,
    "memory_freed_mb": 42.6
  }
}
```

##### Example Request

```bash
curl -X POST "http://localhost:8000/clear-embedding-cache" -H "Content-Type: application/json"
```

#### API Health Check

**GET** `/health`

Simple health check to confirm the API is running and functioning properly.

##### Response

```json
{
  "status": "ok",
  "message": "API is running",
  "version": "1.2.0",
  "uptime_seconds": 3600,
  "system_info": {
    "cpu_usage": "23%",
    "memory_usage": "512MB",
    "embedding_model": "loaded"
  }
}
```

##### Example Request

```bash
curl -X GET "http://localhost:8000/health" -H "Accept: application/json"
```

## 📊 Performance Considerations

### Resource Usage

- **Memory**: The API loads embedding models and index into memory:
  - Base memory usage: ~300-500MB
  - Embedding model: ~200-400MB (depends on model size)
  - FAISS index: ~50MB-2GB (depends on vector count and index type)
  
- **CPU**: Embedding generation is CPU-intensive
  - Consider GPU acceleration for high-traffic deployments
  - Each search query requires ~50-200ms of CPU time

### Optimization Strategies

1. **Embedding Cache**:
   - Default cache size: 1000 entries
   - Adjust with environment variable: `EMBEDDING_CACHE_SIZE=2000`
   - Persistent cache between restarts for common queries

2. **Worker Configuration**:
   - General recommendation: `workers = 2 * CPU_CORES + 1`
   - Memory-limited systems: Use fewer workers
   - High-throughput systems: Increase worker count

3. **Index Types**:
   - Default: Flat index (exact search, higher memory usage)
   - For larger datasets: Consider HNSW or IVF indexes (approximate search, faster)

4. **Horizontal Scaling**:
   - Deploy behind a load balancer
   - Use shared caching layer (Redis) for embedding cache

### Performance Monitoring

- Use the `show_metrics` parameter to measure response times
- Monitor `/health` endpoint for system resource usage
- Consider integrating with Prometheus/Grafana for metrics collection

## 🔧 Error Handling

### HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid input parameters |
| 404 | Not Found | Endpoint doesn't exist |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Server overloaded or maintenance |

### Error Response Format

```json
{
  "error": true,
  "status_code": 400,
  "message": "Invalid search mode. Allowed values: standard, strict, relaxed",
  "request_id": "7f82c53e-4a9c-4ca3-a1bd-3d184b1a3a1c",
  "details": {
    "parameter": "search_mode",
    "value": "unknown",
    "allowed_values": ["standard", "strict", "relaxed"]
  }
}
```

### Common Error Scenarios

1. **Invalid search mode**:
   ```json
   {"error": true, "message": "Invalid search mode. Allowed values: standard, strict, relaxed"}
   ```

2. **Empty query**:
   ```json
   {"error": true, "message": "Query string cannot be empty"}
   ```

3. **Result count out of range**:
   ```json
   {"error": true, "message": "Result count must be between 1 and 100"}
   ```

4. **Model loading failure**:
   ```json
   {"error": true, "message": "Failed to load embedding model", "details": {"reason": "Out of memory"}}
   ```

## 👨‍💻 Development

### Development Environment Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Start with hot reloading enabled
python start_api.py --reload --log-level debug
```

### Embedding Model Selection

The API supports different sentence-transformer models. Change the model by setting environment variables:

```bash
# Set a different embedding model (default is all-MiniLM-L6-v2)
export EMBEDDING_MODEL="paraphrase-multilingual-MiniLM-L12-v2"
python start_api.py
```

### Code Structure

- `start_api.py`: Main entry point
- `api/`: Core API modules
  - `main.py`: FastAPI application and route definitions
  - `search.py`: Search functionality and vector operations
  - `models.py`: Pydantic models for request/response validation
  - `embedding.py`: Text embedding functionality
  - `index.py`: FAISS index management

### Adding New Endpoints

Follow this pattern when adding new endpoints:

```python
@app.get("/new-endpoint", tags=["custom"])
async def new_endpoint(param: str = Query(..., description="Parameter description")):
    # Implementation
    return {"result": "value"}
```

## 🧪 Testing

### Manual Testing with Swagger UI

The interactive Swagger UI at `http://localhost:8000/docs` allows testing all endpoints directly from the browser.

### Using curl

```bash
# Basic search
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "software development"}'

# Search with all options
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{
           "query": "restaurant serving fast food", 
           "result_count": 5, 
           "search_mode": "relaxed", 
           "show_metrics": true
         }'

# Health check
curl -X GET "http://localhost:8000/health"
```

### Automated Testing

Run the test suite:

```bash
pytest tests/
```

Or specific test files:

```bash
pytest tests/test_search.py
```

## 🚢 Deployment Recommendations

### Docker Deployment

A Dockerfile is provided for containerized deployment:

```bash
# Build the Docker image
docker build -t nic-semantic-search-api .

# Run the container
docker run -p 8000:8000 nic-semantic-search-api
```

### Environment Variables

Configure the API using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `HOST` | Bind address | `0.0.0.0` |
| `WORKERS` | Number of worker processes | `4` |
| `LOG_LEVEL` | Logging level | `info` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `EMBEDDING_CACHE_SIZE` | Size of embedding cache | `1000` |
| `INDEX_PATH` | Path to FAISS index file | `./data/faiss_index.bin` |

### Production Deployment

For production environments:

1. Use a reverse proxy (Nginx, Apache) in front of the API
2. Set up rate limiting to prevent abuse
3. Enable HTTPS with proper certificates
4. Consider using managed services (AWS ECS, Azure Container Instances, etc.)
5. Set up monitoring and alerting

## 🔒 Security Considerations

### API Security

- The API doesn't implement authentication by default
- For public deployment, consider adding:
  - API key authentication
  - Rate limiting
  - JWT authentication for admin endpoints

### Data Protection

- No sensitive data is stored by default
- Query logs might contain business information
- Consider implementing:
  - Query logging controls
  - Regular log rotation
  - Data retention policies

### Implementation Example

For basic API key protection:

```python
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-secret-key"
api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/search")
async def search(
    query: SearchQuery,
    api_key: str = Security(api_key_header)
):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    # Process search
```

## 📝 License

This project is licensed under the terms of the MIT license.
