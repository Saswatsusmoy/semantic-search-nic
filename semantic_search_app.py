from flask import Flask, render_template, request, jsonify
import pymongo
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
import logging
import traceback
import json
import os  # Added import for OS functions
import time
from faiss_index_manager import FAISSIndexManager
from bson.objectid import ObjectId
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Get MongoDB connection string from environment
connection_string = os.environ.get("MONGO_URI")
if not connection_string:
    logger.warning("MONGO_URI not found in environment variables. Set this in your .env file.")

# Initialize the FAISS index manager
faiss_manager = FAISSIndexManager(connection_string)

def connect_to_mongodb():
    """
    Connect to MongoDB Atlas and return the client and collection objects.
    """
    try:
        # MongoDB Atlas connection parameters from environment
        connection_string = os.environ.get("MONGO_URI")
        if not connection_string:
            logger.error("MongoDB connection string not found in environment variables")
            raise ValueError("MONGO_URI not set in environment variables")
            
        database_name = os.environ.get("DB_NAME", "NIC_Database")
        collection_name = os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        # Connect to MongoDB Atlas with timeout settings
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        # Test connection explicitly
        client.server_info()
        
        db = client[database_name]
        collection = db[collection_name]
        logger.info(f"Successfully connected to MongoDB Atlas: {database_name}.{collection_name}")
        return client, collection
    except pymongo.errors.ServerSelectionTimeoutError as e:
        logger.error(f"MongoDB server selection timeout: {str(e)}")
        raise
    except pymongo.errors.ConnectionFailure as e:
        logger.error(f"MongoDB connection failure: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {str(e)}")
        logger.error(traceback.format_exc())
        raise

def validate_result_format(result):
    """
    Validate and clean the result format to ensure it's JSON serializable.
    """
    try:
        # Check if fields are present and have valid types
        cleaned = {
            "Section": str(result.get("Section", "N/A")),
            "Division": str(result.get("Division", "N/A")),
            "Group": str(result.get("Group", "N/A")),
            "Class": str(result.get("Class", "N/A")),
            "Sub-Class": str(result.get("Sub-Class", "N/A")),
            "Description": str(result.get("Description", "No description available")),
            "similarity": float(result.get("similarity", 0.0))
        }
        return cleaned
    except Exception as e:
        logger.error(f"Error validating result format: {str(e)}")
        # Return a minimal valid result with error information
        return {
            "NIC_Code": "ERROR",
            "Section": "N/A",
            "Division": "N/A",
            "Group": "N/A", 
            "Class": "N/A",
            "Sub-Class": "N/A",
            "Description": f"Error formatting result: {str(e)}",
            "similarity": 0.0
        }

def perform_semantic_search(query, collection, top_n=10, search_mode="standard"):
    """
    Perform semantic search using FAISS with cosine similarity.
    
    Args:
        query (str): The search query
        collection: MongoDB collection
        top_n (int): Number of results to return
        search_mode (str): Search mode - "standard", "strict", or "relaxed"
        
    Returns:
        list: List of search results
        dict: Performance metrics
    """
    try:
        start_time = time.time()
        metrics = {
            "total_time_ms": 0,
            "index_time_ms": 0,
            "results_count": 0
        }
        
        # Ensure FAISS index is loaded
        if not faiss_manager.index:
            index_load_start = time.time()
            success = faiss_manager.load_index()
            if not success:
                logger.warning("Failed to load FAISS index, building it now...")
                success = faiss_manager.build_index()
                if not success:
                    logger.error("Failed to build FAISS index")
                    return [], metrics
            metrics["index_time_ms"] = int((time.time() - index_load_start) * 1000)
        else:
            metrics["index_time_ms"] = 0  # Index was already loaded
        
        # Encode the query text
        query_embedding = model.encode(query)
        
        # Adjust search parameters based on mode
        if search_mode == "strict":
            # For strict mode, we'll get more results and filter more aggressively
            faiss_results = top_n * 3
            min_similarity = 0.7  # Higher threshold for strict mode
        elif search_mode == "relaxed":
            # For relaxed mode, get even more results and filter less
            faiss_results = top_n * 4
            min_similarity = 0.3  # Lower threshold for relaxed mode
        else:
            # Standard mode
            faiss_results = top_n * 2
            min_similarity = 0.5
        
        # Search start time (after index is loaded)
        search_start = time.time()
        
        # Search using FAISS (with cosine similarity)
        search_results = faiss_manager.search(query_embedding, top_k=faiss_results)
        
        if not search_results:
            logger.warning("No search results returned from FAISS")
            metrics["total_time_ms"] = int((time.time() - start_time) * 1000)
            return [], metrics
        
        # Get document IDs and similarity scores
        # In cosine similarity, scores range from -1 to 1, with 1 being perfect similarity
        doc_ids = [ObjectId(doc_id) for doc_id, _ in search_results]
        similarity_dict = {str(doc_id): sim for doc_id, sim in search_results}
        
        # Fetch documents from MongoDB
        documents = list(collection.find({"_id": {"$in": doc_ids}}))
        logger.info(f"Found {len(documents)} documents from FAISS search results")
        metrics["results_count"] = len(documents)
        
        results = []
        for doc in documents:
            try:
                # Include the document if it has valid Class (even if Sub-Class is invalid)
                class_val = doc.get("Class")
                is_valid = False
                
                # Check for valid Sub-Class
                subclass_val = doc.get("Sub-Class")
                if subclass_val and str(subclass_val).strip() and str(subclass_val).lower() != "nan":
                    is_valid = True
                # Check for valid Class if Sub-Class is invalid
                elif class_val and str(class_val).strip() and str(class_val).lower() != "nan":
                    is_valid = True
                    
                # Skip document if neither Class nor Sub-Class is valid
                if not is_valid:
                    logger.debug(f"Skipping document with no valid Class or Sub-Class: {doc.get('_id')}")
                    continue
                
                # Look up similarity score from our results
                similarity = similarity_dict.get(str(doc["_id"]), 0.0)
                
                # Apply similarity threshold filtering based on search mode
                if similarity < min_similarity:
                    continue
                
                # Add relevant information and similarity score
                result = {
                    "NIC_Code": doc.get("NIC", "N/A"),
                    "Section": doc.get("Section", "N/A"),
                    "Division": doc.get("Divison", "N/A"),
                    "Group": doc.get("Group", "N/A"),
                    "Class": doc.get("Class", "N/A"),
                    "Sub-Class": doc.get("Sub-Class", "N/A"),
                    "Description": doc.get("Description", "N/A"),
                    "similarity": float(similarity)
                }
                results.append(result)
            except Exception as e:
                # Log error but continue with other documents
                logger.error(f"Error processing document: {str(e)}")
                continue
        
        # Sort by similarity score and get top N
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Validate the top results to ensure they're JSON serializable
        validated_results = [validate_result_format(res) for res in results[:top_n]]
        
        # Calculate total search time
        metrics["total_time_ms"] = int((time.time() - start_time) * 1000)
        
        logger.info(f"Found {len(validated_results)} results with valid fields in {metrics['total_time_ms']}ms")
        return validated_results, metrics
        
    except Exception as e:
        logger.error(f"Error performing semantic search: {str(e)}")
        logger.error(traceback.format_exc())
        metrics["total_time_ms"] = int((time.time() - start_time) * 1000)
        return [], metrics

@app.route('/')
def index():
    """Render the main search page"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search query and return results"""
    client = None
    try:
        # Get query from request
        query = request.form.get('query', '')
        result_count = int(request.form.get('result_count', 10))
        search_mode = request.form.get('search_mode', 'standard')
        show_metrics = request.form.get('show_metrics', 'false') == 'true'
        
        if not query.strip():
            return jsonify({"error": "Empty query", "results": []})
        
        logger.info(f"Processing search query: '{query}' (mode: {search_mode}, results: {result_count})")
        
        # Connect to MongoDB
        client, collection = connect_to_mongodb()
        
        # Perform semantic search with cosine similarity
        results, metrics = perform_semantic_search(
            query, 
            collection, 
            top_n=result_count,
            search_mode=search_mode
        )
        
        logger.info(f"Found {len(results)} results for query: '{query}'")
        
        # Prepare response
        response = {"results": results}
        
        # Add performance metrics if requested
        if show_metrics:
            response["metrics"] = metrics
        
        # Test JSON serialization before returning
        try:
            # Test that the response can be serialized to JSON
            json.dumps(response)
            return jsonify(response)
        except (TypeError, ValueError) as json_err:
            logger.error(f"JSON serialization error: {str(json_err)}")
            # Return a simplified response that will definitely be JSON serializable
            simplified_results = [{"NIC_Code": "ERROR", "Description": "JSON serialization error", "similarity": 0.0}]
            return jsonify({"error": "Results format error", "results": simplified_results})
    
    except Exception as e:
        error_msg = f"Error processing search: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return jsonify({"error": error_msg, "results": []})
    finally:
        # Ensure MongoDB connection is closed even if an exception occurs
        if client:
            try:
                client.close()
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")

@app.route('/rebuild-index', methods=['POST'])
def rebuild_index():
    """Admin endpoint to rebuild the FAISS index"""
    try:
        success = faiss_manager.build_index(force_rebuild=True)
        if success:
            return jsonify({"status": "success", "message": "Index rebuilt successfully with cosine similarity"})
        else:
            return jsonify({"status": "error", "message": "Failed to rebuild index"})
    except Exception as e:
        error_msg = f"Error rebuilding index: {str(e)}"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": error_msg})

@app.route('/get-index-stats', methods=['GET'])
def get_index_stats():
    """Admin endpoint to get FAISS index statistics"""
    try:
        if not faiss_manager.index:
            success = faiss_manager.load_index()
            if not success:
                return jsonify({
                    "status": "error", 
                    "message": "Index not loaded and could not be loaded from disk"
                })
        
        stats = {
            "vector_count": faiss_manager.index.ntotal,
            "index_type": "Flat Inner Product (Cosine Similarity)",
            "dimension": faiss_manager.index.d,
            "index_file_exists": os.path.exists(faiss_manager.index_path),
            "id_map_file_exists": os.path.exists(faiss_manager.id_map_path)
        }
        
        if hasattr(faiss_manager.index, "id_map") and faiss_manager.index.id_map is not None:
            stats["id_map_size"] = len(faiss_manager.id_map)
        
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        error_msg = f"Error getting index stats: {str(e)}"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": error_msg})

if __name__ == '__main__':
    # Load the FAISS index on startup
    logger.info("Loading FAISS index...")
    success = faiss_manager.load_index()
    if not success:
        logger.warning("FAISS index not found or could not be loaded. Building index...")
        faiss_manager.build_index()
    
    app.run(debug=True)
