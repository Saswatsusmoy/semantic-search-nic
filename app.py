"""
Flask application for NIC Codes Semantic Search
Provides API routes for searching and admin functions
"""

import os
import time
import json
from typing import Dict, Any, List
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

# Import custom modules
from faiss_index_manager import FAISSIndexManager
from vector_embeddings_manager import cached_get_embedding, get_embeddings_manager
import recording

# Load environment variables
load_dotenv()

# Configure the application
app = Flask(__name__, static_folder='static')
CORS(app)  # Allow cross-origin requests
app.config['JSON_SORT_KEYS'] = False

# Initialize MongoDB connection
mongo_uri = os.environ.get("MONGO_URI")
db_name = os.environ.get("DB_NAME", "NIC_Database")
collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")

# Initialize FAISS manager
faiss_manager = FAISSIndexManager(mongo_uri, db_name, collection_name)

# Ensure index is loaded on startup
if not faiss_manager.load_index():
    # If index doesn't exist or fails to load, build it
    faiss_manager.build_index()

def get_mongodb_collection():
    """Get MongoDB collection for NIC codes"""
    client = MongoClient(mongo_uri)
    db = client[db_name]
    return client, db[collection_name]

def format_search_results(raw_results: List[tuple], mongo_collection) -> List[Dict[str, Any]]:
    """Format search results with document data from MongoDB
    
    Args:
        raw_results: List of (doc_id, similarity) tuples from FAISS search
        mongo_collection: MongoDB collection to fetch documents from
        
    Returns:
        List of formatted search results with document data
    """
    results = []
    
    # Get document IDs to fetch
    doc_ids = [ObjectId(doc_id) for doc_id, _ in raw_results]
    
    # Fetch documents from MongoDB
    documents = list(mongo_collection.find({"_id": {"$in": doc_ids}}))
    
    # Create a mapping of document IDs to documents
    doc_map = {str(doc["_id"]): doc for doc in documents}
    
    # Build formatted results
    for doc_id, similarity in raw_results:
        if doc_id in doc_map:
            doc = doc_map[doc_id]
            
            # Calculate similarity percentage (0-100%)
            similarity_percent = int(max(0, min(100, similarity * 100)))
            
            # Format document data for response
            result = {
                "id": str(doc["_id"]),
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
    
    return results

@app.route('/')
def index():
    """Render the main search page"""
    return send_from_directory('static', 'index.html')

@app.route('/search', methods=['POST'])
def search():
    """Search NIC codes using semantic search"""
    start_time = time.time()
    
    # Get search parameters
    query = request.form.get('query', '')
    result_count = int(request.form.get('result_count', 10))
    search_mode = request.form.get('search_mode', 'standard')
    show_metrics = request.form.get('show_metrics') == 'true'
    
    # Handle empty query
    if not query:
        return jsonify({"error": "Empty query", "results": []})
    
    try:
        # Get query embedding
        model_name = 'all-MiniLM-L6-v2'
        embedding_start = time.time()
        query_embedding = cached_get_embedding(query, model_name)
        embedding_time = time.time() - embedding_start
        
        # Perform search
        index_start = time.time()
        raw_results = faiss_manager.search(query_embedding, result_count)
        index_time = time.time() - index_start
        
        # Get full documents from MongoDB
        client, collection = get_mongodb_collection()
        formatted_results = format_search_results(raw_results, collection)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Prepare response
        response = {
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
        # Include performance metrics if requested
        if show_metrics:
            response["metrics"] = {
                "total_time_ms": round(total_time * 1000, 2),
                "embedding_time_ms": round(embedding_time * 1000, 2),
                "index_time_ms": round(index_time * 1000, 2),
                "results_count": len(raw_results)
            }
        
        client.close()
        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f"Search error: {str(e)}")
        return jsonify({"error": str(e), "results": []})

@app.route('/rebuild-index', methods=['POST'])
def rebuild_index():
    """Rebuild the FAISS index"""
    try:
        start_time = time.time()
        success = faiss_manager.build_index(force_rebuild=True)
        build_time = time.time() - start_time
        
        if success:
            return jsonify({
                "status": "success",
                "message": "FAISS index rebuilt successfully",
                "time_taken": round(build_time, 2)
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to rebuild FAISS index"
            })
    except Exception as e:
        app.logger.error(f"Rebuild index error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        })

@app.route('/get-index-stats', methods=['GET'])
def get_index_stats():
    """Get statistics about the FAISS index"""
    try:
        # Load index if not loaded
        if faiss_manager.index is None:
            faiss_manager.load_index()
        
        if faiss_manager.index is None:
            return jsonify({
                "status": "error",
                "message": "FAISS index not available"
            })
        
        # Get embedding manager stats
        embedding_manager = get_embeddings_manager()
        embedding_stats = embedding_manager.get_stats()
        
        # Compile stats
        stats = {
            "index_size": faiss_manager.index.ntotal,
            "id_map_size": len(faiss_manager.id_map) if faiss_manager.id_map else 0,
            "embedding_cache_size": embedding_stats["cache_size"],
            "embedding_cache_hit_rate": f"{embedding_stats['hit_rate']:.2%}",
            "embedding_requests": embedding_stats["total_requests"]
        }
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        app.logger.error(f"Get index stats error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        })

@app.route('/clear-embedding-cache', methods=['POST'])
def clear_embedding_cache():
    """Clear the embedding cache"""
    try:
        embedding_manager = get_embeddings_manager()
        embedding_manager.clear_cache()
        return jsonify({
            "status": "success",
            "message": "Embedding cache cleared successfully"
        })
    except Exception as e:
        app.logger.error(f"Clear cache error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Error: {str(e)}"
        })

@app.route('/api/start_recording', methods=['POST'])
def start_recording_endpoint():
    recording.start_recording()
    return jsonify({"status": "success", "message": "Recording started"})

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording_endpoint():
    output_filename = "Data Processing/output.wav"
    transcript = recording.stop_recording(output_filename)
    return jsonify({"status": "success", "message": "Recording stopped", "transcript": transcript})

if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs("Data Processing", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
