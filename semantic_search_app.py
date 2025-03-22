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
<<<<<<< HEAD
# from cleaning import clean_sentence  # Added import for clean_sentence function
from recording import start_recording, stop_recording  # Import recording functions
=======
from cleaning import correct_words  # Added import for clean_sentence function
>>>>>>> 6ac000741034e68e46a29bb6be620b3aa94a4ec9

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Path to local JSON file
json_file_path = os.path.join(os.path.dirname(__file__), "output.json")

# Initialize the FAISS index manager
faiss_manager = FAISSIndexManager()  # No need for connection string now

# Global variable to store data from JSON file
json_data = []

def load_json_data():
    """
    Load data from local JSON file
    
    Returns:
        list: List of documents from the JSON file
    """
    global json_data
    try:
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r', encoding='utf-8') as file:
                json_data = json.load(file)
            logger.info(f"Successfully loaded {len(json_data)} documents from {json_file_path}")
            return json_data
        else:
            logger.error(f"JSON file not found: {json_file_path}")
            return []
    except Exception as e:
        logger.error(f"Error loading JSON file: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def connect_to_mongodb():
    """
    Load data from local JSON file instead of connecting to MongoDB
    
    Returns:
        tuple: (None, data_accessor) where data_accessor provides MongoDB-like functionality
    """
    try:
        # Ensure data is loaded
        if not json_data:
            load_json_data()
            
        # Create a simple class that mimics MongoDB collection functionality
        class LocalDataAccessor:
            def find(self, query=None, projection=None):
                """Mimic MongoDB find() function"""
                results = []
                for doc in json_data:
                    # Simple query matching
                    if query:
                        # Handle _id query
                        if "_id" in query and "$in" in query["_id"]:
                            id_list = [str(id) for id in query["_id"]["$in"]]
                            if str(doc.get("_id")) not in id_list:
                                continue
                        # Handle field exists query
                        for field, value in query.items():
                            if isinstance(value, dict) and "$exists" in value:
                                if value["$exists"] and field not in doc:
                                    continue
                    
                    # Handle projection
                    if projection:
                        result = {}
                        for field, include in projection.items():
                            if include and field in doc:
                                result[field] = doc[field]
                        results.append(result)
                    else:
                        results.append(doc)
                return results
                
        logger.info(f"Using local data accessor with {len(json_data)} documents")
        return None, LocalDataAccessor()
    except Exception as e:
        logger.error(f"Failed to set up local data accessor: {str(e)}")
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
        collection: Local data accessor that mimics MongoDB collection
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
        
        #Clean and spellcorrect query
        query = correct_words(query)
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
        doc_ids = [doc_id for doc_id, _ in search_results]
        similarity_dict = {doc_id: sim for doc_id, sim in search_results}
        
        # Fetch documents from local data
        all_documents = collection.find()
        documents = [doc for doc in all_documents if str(doc.get("_id")) in doc_ids]
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
    try:
        # Get query from request
        query = request.form.get('query', '')
        result_count = int(request.form.get('result_count', 10))
        search_mode = request.form.get('search_mode', 'standard')
        show_metrics = request.form.get('show_metrics', 'false') == 'true'
        
        if not query.strip():
            return jsonify({"error": "Empty query", "results": []})
        
        logger.info(f"Processing search query: '{query}' (mode: {search_mode}, results: {result_count})")
        
        # Get local data instead of MongoDB connection
        _, collection = connect_to_mongodb()
        
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

@app.route('/rebuild-index', methods=['POST'])
def rebuild_index():
    """Admin endpoint to rebuild the FAISS index"""
    try:
        # Make sure we have the data loaded
        if not json_data:
            load_json_data()
            
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

@app.route('/api/start_recording', methods=['POST'])
def start_recording_endpoint():
    start_recording()
    return jsonify({"status": "success", "message": "Recording started"})

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording_endpoint():
    output_filename = "Data Processing/output.wav"
    transcript = stop_recording(output_filename)
    return jsonify({"status": "success", "message": "Recording stopped", "transcript": transcript})

if __name__ == '__main__':
    # Load the JSON data on startup
    logger.info("Loading data from JSON file...")
    load_json_data()
    
    # Load the FAISS index on startup
    logger.info("Loading FAISS index...")
    success = faiss_manager.load_index()
    if not success:
        logger.warning("FAISS index not found or could not be loaded. Building index...")
        faiss_manager.build_index()
    
    # Ensure the output directory exists
    os.makedirs("Data Processing", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
