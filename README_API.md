# NIC Code Semantic Search API

This document describes the FastAPI-based REST API for the NIC Code Semantic Search application.

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- MongoDB Atlas account (or local MongoDB installation)
- Required Python packages (see `requirements.txt`)

### Running the API

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
python start_api.py

# Or with options
python start_api.py --host 127.0.0.1 --port 8000 --reload --workers 4
```

The API will be available at:
- API and interactive documentation: `http://localhost:8000/`
- Alternative API docs: `http://localhost:8000/redoc`

## 📚 API Endpoints

### Search Endpoint

**POST** `/search`

Search for NIC codes using semantic similarity.

**Request Body (JSON):**
```json
{
  "query": "software development",
  "result_count": 10,
  "search_mode": "standard",
  "show_metrics": true
}
```

**Parameters:**
- `query` (string, required): The search query text
- `result_count` (integer, optional, default=10): Number of results to return (1-100)
- `search_mode` (string, optional, default="standard"): Search mode - "standard", "strict", or "relaxed"
- `show_metrics` (boolean, optional, default=false): Include performance metrics in the response

**Response:**
```json
{
  "results": [
    {
      "id": "...",
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
    ...
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

### Admin Endpoints

#### Rebuild Index

**POST** `/rebuild-index`

Rebuilds the FAISS index from scratch.

**Response:**
```json
{
  "status": "success",
  "message": "Index rebuilt successfully",
  "time_taken": 3.45
}
```

#### Get Index Statistics

**GET** `/get-index-stats`

Returns information about the current state of the FAISS index.

**Response:**
```json
{
  "vector_count": 23456,
  "index_type": "Flat Inner Product (Cosine Similarity)",
  "dimension": 384,
  "index_file_exists": true,
  "id_map_file_exists": true,
  "id_map_size": 23456,
  "embedding_cache_size": 120,
  "embedding_cache_hit_rate": "85.5%",
  "embedding_requests": 250
}
```

#### Clear Embedding Cache

**POST** `/clear-embedding-cache`

Clears the in-memory and disk cache of embeddings.

**Response:**
```json
{
  "status": "success",
  "message": "Embedding cache cleared successfully"
}
```

#### API Health Check

**GET** `/health`

Simple health check to confirm the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "API is running"
}
```

## 📊 Performance Considerations

- The API is designed to handle multiple concurrent requests
- For high-traffic deployments, increase the number of workers
- First-time searches might be slower as models are loaded into memory
- Consider using a load balancer for horizontal scaling

## 🔧 Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Request successful
- `400 Bad Request`: Invalid input parameters
- `500 Internal Server Error`: Server-side processing error

Error responses include a detail message explaining the issue.

## 👨‍💻 Development

For development, start the server with the `--reload` flag:

```bash
python start_api.py --reload
```

This will automatically reload the server when code changes are detected.

## 🧪 Testing the API

You can test the API directly from the interactive Swagger UI at `http://localhost:8000/` or use tools like curl or Postman:

```bash
# Example curl command to search
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "software development", "result_count": 5, "search_mode": "standard", "show_metrics": true}'
```
