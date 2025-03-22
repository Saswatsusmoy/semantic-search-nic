"""
FastAPI application for NIC Codes Semantic Search
Provides high-performance API routes for searching and admin functions
"""

import os
import time
import json
import traceback
from typing import Dict, Any, List, Optional, Union
import logging
from fastapi import FastAPI, Depends, HTTPException, Query, Form, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
# No need for MongoDB imports
from dotenv import load_dotenv

# Import custom modules
from faiss_index_manager import FAISSIndexManager
from vector_embeddings_manager import cached_get_embedding, get_embeddings_manager
from flask_compat import configure_templates

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")
# Add Flask-compatible functions to templates
templates = configure_templates(templates)

# Load environment variables
load_dotenv()

# Configure the application
app = FastAPI(
    title="NIC Code Semantic Search API",
    description="API for semantic search of National Industrial Classification (NIC) codes using FAISS",
    version="1.0.0",
    docs_url="/",  # Make Swagger UI the root page
    redoc_url="/redoc"
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Path to local JSON file
json_file_path = os.path.join(os.path.dirname(__file__), "output.json")

# Global variable to store data from JSON file
json_data = []

# Load JSON data
def load_json_data():
    """Load data from local JSON file"""
    global json_data
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            json_data = json.load(file)
        logger.info(f"Loaded {len(json_data)} records from JSON file")
        return True
    except Exception as e:
        logger.error(f"Error loading JSON data: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# Initialize FAISS manager with the JSON file path
faiss_manager = FAISSIndexManager(json_file_path=json_file_path)

# Ensure index is loaded on startup
@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup"""
    # Load JSON data
    if not load_json_data():
        logger.error("Failed to load JSON data, API may not function correctly")
        return
    
    logger.info(f"Loaded {len(json_data)} documents from JSON file")
    
    # Load FAISS index or build a new one
    if not faiss_manager.load_index():
        # If index doesn't exist or fails to load, build it
        logger.info("Building FAISS index on startup from JSON data")
        if faiss_manager.build_index(force_rebuild=True):
            logger.info("FAISS index built successfully")
        else:
            logger.error("Failed to build FAISS index")
            return
    else:
        logger.info("FAISS index loaded successfully")

# Pydantic models for request/response validation
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query text")
    result_count: int = Field(10, description="Number of results to return", ge=1, le=100)
    search_mode: str = Field("standard", description="Search mode: 'standard', 'strict', or 'relaxed'")
    show_metrics: bool = Field(False, description="Include performance metrics in the response")

class SearchResult(BaseModel):
    id: str
    title: str
    description: str
    section: str = ""
    section_description: str = ""
    division: str = ""
    division_description: str = ""
    group: str = ""
    group_description: str = ""
    class_code: str = Field("", alias="class")
    class_description: str = ""
    subclass: str = ""
    subclass_description: str = ""
    similarity: float
    similarity_percent: float
    
    class Config:
        allow_population_by_field_name = True

class SearchMetrics(BaseModel):
    total_time_ms: float
    embedding_time_ms: float
    index_time_ms: float
    results_count: int

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]  # Changed from List[SearchResult] for flexibility
    count: int
    metrics: Optional[Dict[str, Any]] = None  # Changed from SearchMetrics for flexibility

    class Config:
        arbitrary_types_allowed = True

class IndexStats(BaseModel):
    vector_count: int
    index_type: str
    dimension: int
    index_file_exists: bool
    id_map_file_exists: bool
    id_map_size: Optional[int] = None
    embedding_cache_size: Optional[int] = None
    embedding_cache_hit_rate: Optional[str] = None
    embedding_requests: Optional[int] = None

class StatusResponse(BaseModel):
    status: str
    message: str
    time_taken: Optional[float] = None

# Get documents by IDs from local JSON data
def get_documents_by_ids(doc_ids):
    """Get documents by ID from local JSON data"""
    documents = []
    for doc in json_data:
        if str(doc.get("_id")) in doc_ids:
            documents.append(doc)
    return documents

# Format search results using local JSON data
def format_search_results(raw_results: List[tuple]) -> List[Dict[str, Any]]:
    """Format raw search results with document data from JSON file"""
    results = []
    
    if not raw_results:
        return results
        
    try:
        # Create a map of document IDs to similarities for efficient lookup
        similarity_map = {doc_id: similarity for doc_id, similarity in raw_results}
        
        # Get document IDs as strings
        doc_ids = [doc_id for doc_id, _ in raw_results]
        
        # Get documents from JSON data
        documents = get_documents_by_ids(doc_ids)
        logger.info(f"Retrieved {len(documents)} documents from JSON data for {len(doc_ids)} result IDs")
        
        for doc in documents:
            doc_id = str(doc["_id"])
            similarity = similarity_map.get(doc_id, 0)
            similarity_percent = round(similarity * 100, 2)
            
            # Format document data for response
            result = {
                "id": doc_id,
                "title": doc.get("Sub-Class_Description", doc.get("Class_Description", "No Title")),
                "section": doc.get("Section", ""),
                "section_description": doc.get("Section_Description", ""),
                "division": doc.get("Division", ""),
                "division_description": doc.get("Division_Description", ""),
                "group": doc.get("Group", ""),
                "group_description": doc.get("Group_Description", ""),
                "class": doc.get("Class", ""),
                "class_description": doc.get("Class_Description", ""),
                "subclass": doc.get("Sub-Class", ""),
                "subclass_description": doc.get("Sub-Class_Description", ""),
                "similarity": similarity,
                "similarity_percent": similarity_percent,
                "description": doc.get("Sub-Class_Description", doc.get("Class_Description", "No description available"))
            }
            
            results.append(result)
        
        # Sort by similarity score (highest first)
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
    except Exception as e:
        logger.error(f"Error formatting search results: {str(e)}")
        logger.error(traceback.format_exc())
        
    return results

# API Routes
@app.get("/ui", response_class=RedirectResponse, include_in_schema=False)
async def legacy_ui():
    """Redirect to the API documentation"""
    return RedirectResponse(url="/")

@app.post("/search", response_model=SearchResponse)
async def search(
    request: Request,
    query: Optional[str] = Form(None),
    result_count: Optional[int] = Form(10),
    search_mode: Optional[str] = Form("standard"),
    show_metrics: Optional[bool] = Form(False)
):
    """
    Search NIC codes using semantic search
    
    This endpoint accepts either JSON or form data and returns matching NIC codes
    ranked by semantic similarity.
    
    - **query**: The search query text (e.g., "software development", "bakery")
    - **result_count**: Number of results to return (1-100)
    - **search_mode**: Search mode - "standard", "strict", or "relaxed"
    - **show_metrics**: Whether to include performance metrics in the response
    
    Returns matched NIC codes with similarity scores and detailed information.
    """
    start_time = time.time()
    
    # Check if this is a JSON request
    content_type = request.headers.get('content-type', '')
    search_request = None
    
    # Debug log to track the request
    logger.info(f"Search request received with content-type: {content_type}")
    
    if 'application/json' in content_type:
        try:
            # Parse JSON input
            data = await request.json()
            logger.info(f"Received JSON data: {data}")
            
            # Create SearchRequest object
            search_request = SearchRequest(
                query=data.get('query'),
                result_count=data.get('result_count', 10),
                search_mode=data.get('search_mode', 'standard'),
                show_metrics=data.get('show_metrics', False)
            )
        except Exception as e:
            logger.error(f"Error parsing JSON request: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    else:
        # Use form data if provided
        if query:
            # Convert boolean string to actual boolean if needed
            if isinstance(show_metrics, str):
                show_metrics = show_metrics.lower() == 'true'
                
            # Create request object from form data
            try:
                search_request = SearchRequest(
                    query=query,
                    result_count=int(result_count),
                    search_mode=search_mode,
                    show_metrics=show_metrics
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid form data: {str(e)}")
                
    # Ensure we have a search request
    if not search_request or not search_request.query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Validate search mode
    valid_modes = ["standard", "strict", "relaxed"]
    if search_request.search_mode not in valid_modes:
        raise HTTPException(status_code=400, detail=f"Invalid search mode. Must be one of: {', '.join(valid_modes)}")
    
    try:
        logger.info(f"Processing search: '{search_request.query}', mode: {search_request.search_mode}")
        
        # Get query embedding
        model_name = 'all-MiniLM-L6-v2'
        embedding_start = time.time()
        query_embedding = cached_get_embedding(search_request.query, model_name)
        embedding_time = time.time() - embedding_start
        
        # Perform search
        index_start = time.time()
        
        # Adjust search parameters based on mode
        search_multiplier = {
            "standard": 2,
            "strict": 3,
            "relaxed": 4
        }.get(search_request.search_mode, 2)
        
        # Get more results than requested to filter later if needed
        raw_results = faiss_manager.search(query_embedding, top_k=search_request.result_count * search_multiplier)
        index_time = time.time() - index_start
        
        # Debug log raw results
        logger.info(f"Raw search results: {len(raw_results)} items found")
        
        # Filter by similarity threshold based on search mode
        thresholds = {
            "standard": 0.5,
            "strict": 0.7,
            "relaxed": 0.3
        }
        threshold = thresholds.get(search_request.search_mode, 0.5)
        
        filtered_results = [(doc_id, sim) for doc_id, sim in raw_results if sim >= threshold]
        logger.info(f"Filtered results: {len(filtered_results)} items after threshold {threshold}")
        
        # Get full documents from local JSON
        formatted_results = format_search_results(filtered_results)
        
        # Take only the requested number
        formatted_results = formatted_results[:search_request.result_count]
        logger.info(f"Final results count: {len(formatted_results)}")
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Prepare response
        response = {
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
        # Include performance metrics if requested
        if search_request.show_metrics:
            response["metrics"] = {
                "total_time_ms": round(total_time * 1000, 2),
                "embedding_time_ms": round(embedding_time * 1000, 2),
                "index_time_ms": round(index_time * 1000, 2),
                "results_count": len(raw_results)
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.post("/rebuild-index", response_model=StatusResponse, tags=["Admin"])
async def rebuild_index():
    """
    Admin endpoint to rebuild the FAISS index
    
    This will rebuild the FAISS index from scratch using all documents in JSON data.
    Use this when you've added new documents or updated existing ones.
    
    Returns success status and time taken to rebuild the index.
    """
    try:
        # Make sure JSON data is loaded
        if not json_data:
            load_json_data()
            
        start_time = time.time()
        success = faiss_manager.build_index(force_rebuild=True)
        build_time = time.time() - start_time
        
        if success:
            return {
                "status": "success", 
                "message": "FAISS index rebuilt successfully",
                "time_taken": round(build_time, 2)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to rebuild index")
    except Exception as e:
        error_msg = f"Error rebuilding index: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.get("/get-index-stats", response_model=IndexStats, tags=["Admin"])
async def get_index_stats():
    """
    Admin endpoint to get FAISS index statistics
    
    Returns information about the current state of the FAISS index including:
    - Vector count
    - Index type
    - Dimension
    - File existence
    - Embedding cache statistics
    """
    try:
        if not faiss_manager.index:
            success = faiss_manager.load_index()
            if not success:
                raise HTTPException(
                    status_code=500, 
                    detail="Index not loaded and could not be loaded from disk"
                )
        
        # Get embedding manager stats
        embedding_manager = get_embeddings_manager()
        embedding_stats = embedding_manager.get_stats() if hasattr(embedding_manager, 'get_stats') else {}
        
        stats = {
            "vector_count": faiss_manager.index.ntotal,
            "index_type": "Flat Inner Product (Cosine Similarity)",
            "dimension": faiss_manager.index.d,
            "index_file_exists": os.path.exists(faiss_manager.index_path),
            "id_map_file_exists": os.path.exists(faiss_manager.id_map_path),
            "embedding_cache_size": embedding_stats.get("cache_size", 0),
            "embedding_cache_hit_rate": f"{embedding_stats.get('hit_rate', 0):.2%}",
            "embedding_requests": embedding_stats.get("total_requests", 0)
        }
        
        if hasattr(faiss_manager, "id_map") and faiss_manager.id_map is not None:
            stats["id_map_size"] = len(faiss_manager.id_map)
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error getting index stats: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/clear-embedding-cache", response_model=StatusResponse, tags=["Admin"])
async def clear_embedding_cache():
    """
    Admin endpoint to clear the embedding cache
    
    Clears the in-memory and disk cache of embeddings to free up memory.
    Use this if you're experiencing memory issues or want to force re-calculation
    of embeddings.
    """
    try:
        from vector_embeddings_manager import clear_cache
        clear_cache()
        return {"status": "success", "message": "Embedding cache cleared successfully"}
    except Exception as e:
        error_msg = f"Error clearing embedding cache: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

# API health check endpoint
@app.get("/health", response_model=StatusResponse, tags=["System"])
async def health_check():
    """
    API health check endpoint
    
    Use this to verify that the API is running properly.
    Returns a simple status message.
    """
    return {"status": "ok", "message": "API is running"}

@app.get("/hindi-search", response_class=HTMLResponse, tags=["UI"])
async def hindi_search_page():
    """
    Hindi search interface page
    
    Returns the HTML interface for Hindi-specific semantic search functionality.
    """
    return templates.TemplateResponse("hindi_search.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)