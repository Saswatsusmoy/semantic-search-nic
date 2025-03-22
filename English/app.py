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

# Add imports for Hindi embeddings
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np

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

# Define global variables for language support
SUPPORTED_LANGUAGES = ["english", "hindi"]
DEFAULT_LANGUAGE = "english"
current_language = DEFAULT_LANGUAGE

# Dictionary to store data and indexes for different languages
language_data = {
    "english": {"data": None, "index": None, "embedding_function": None},
    "hindi": {"data": None, "index": None, "embedding_function": None, "documents": [], "id_map": {}}
}

# Hindi embedding model
hindi_model_name = "krutrim-ai-labs/Vyakyarth"
hindi_tokenizer = None
hindi_model = None

# Function to get Hindi embeddings using krutrim-ai-labs/Vyakyarth
def get_hindi_embeddings(texts):
    global hindi_tokenizer, hindi_model
    
    # Initialize the model if not already done
    if hindi_tokenizer is None or hindi_model is None:
        try:
            hindi_tokenizer = AutoTokenizer.from_pretrained(hindi_model_name)
            hindi_model = AutoModel.from_pretrained(hindi_model_name)
            hindi_model.eval()
        except Exception as e:
            print(f"Error loading Hindi embedding model: {e}")
            return None
    
    # Preprocess Hindi text to improve matching
    processed_texts = []
    for text in texts:
        # Remove unnecessary spaces and normalize
        text = ' '.join(text.split())
        # Add any Hindi-specific preprocessing here
        processed_texts.append(text)
    
    # Process texts in batches
    embeddings = []
    try:
        with torch.no_grad():
            for text in processed_texts:
                inputs = hindi_tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                outputs = hindi_model(**inputs)
                
                # Use attention-weighted pooling for better semantic representation
                # Get the last hidden state
                last_hidden_state = outputs.last_hidden_state
                
                # Get attention mask to avoid padding tokens
                attention_mask = inputs['attention_mask']
                
                # Apply attention mask to last hidden state (broadcast to feature dim)
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
                
                # Sum the masked hidden state
                sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                
                # Get the mean pooled vector
                embedding = (sum_embeddings / sum_mask).squeeze().numpy()
                embeddings.append(embedding)
    except Exception as e:
        print(f"Error generating Hindi embeddings: {e}")
        return None
    
    return np.array(embeddings)

# Function to load Hindi embeddings from output_hindi.json
def load_hindi_embeddings():
    try:
        hindi_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_hindi.json")
        
        if not os.path.exists(hindi_file_path):
            print(f"Hindi embeddings file not found at {hindi_file_path}")
            return None, None, None
        
        print(f"Loading Hindi embeddings from {hindi_file_path}")
        with open(hindi_file_path, 'r', encoding='utf-8') as f:
            hindi_data = json.load(f)
        
        # Process Hindi data
        hindi_documents = []
        hindi_embeddings = []
        id_map = {}
        
        for i, doc in enumerate(hindi_data):
            if "embeddings" in doc and doc["embeddings"]:
                hindi_documents.append(doc)
                hindi_embeddings.append(doc["embeddings"])
                id_map[i] = str(doc["_id"])
        
        # Convert to numpy array
        hindi_embeddings_array = np.array(hindi_embeddings, dtype=np.float32)
        
        print(f"Loaded {len(hindi_documents)} Hindi documents with embeddings")
        return hindi_documents, hindi_embeddings_array, id_map
    
    except Exception as e:
        print(f"Error loading Hindi embeddings: {e}")
        return None, None, None

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
    
    # Get search parameters from JSON request body
    if request.is_json:
        data = request.get_json()
        query = data.get('query', '')
        result_count = int(data.get('count', 10))
        search_mode = data.get('mode', 'standard')
        show_metrics = data.get('metrics', False)
        language = data.get('language', current_language)
    else:
        # Legacy form data support
        query = request.form.get('query', '')
        result_count = int(request.form.get('result_count', 10))
        search_mode = request.form.get('search_mode', 'standard')
        show_metrics = request.form.get('show_metrics') == 'true'
        language = request.form.get('language', current_language)
    
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    # Handle empty query
    if not query:
        return jsonify({"error": "Empty query", "results": []})
    
    try:
        # Use language-specific embedding function and index
        embedding_function = language_data[language]["embedding_function"]
        index = language_data[language]["index"]
        
        if not index or not embedding_function:
            return jsonify({"error": "Language not properly initialized", "results": []})
        
        # Get query embedding
        embedding_start = time.time()
        query_embedding = embedding_function([query])[0].reshape(1, -1)
        embedding_time = time.time() - embedding_start
        
        # Perform search
        index_start = time.time()
        distances, indices = index.search(query_embedding, result_count)
        index_time = time.time() - index_start
        
        # Get full documents and format results
        if language == "hindi" and language_data["hindi"]["documents"]:
            # For Hindi with pre-loaded documents
            id_map = language_data["hindi"]["id_map"]
            documents = language_data["hindi"]["documents"]
            
            raw_results = [(id_map[int(idx)], 1.0 - float(distances[0][i])) 
                         for i, idx in enumerate(indices[0]) if idx >= 0 and int(idx) in id_map]
            
            # Format results directly from loaded documents
            formatted_results = []
            for doc_id, similarity in raw_results:
                # Find the document with matching ID
                doc = next((d for d in documents if str(d["_id"]) == doc_id), None)
                if doc:
                    # Calculate similarity percentage
                    similarity_percent = int(max(0, min(100, similarity * 100)))
                    
                    # Format document data for response
                    result = {
                        "id": str(doc["_id"]),
                        "title": doc.get("Description", "No Title"),
                        "section": doc.get("Section", ""),
                        "division": doc.get("Divison", ""),  # Note the typo in the JSON schema
                        "group": doc.get("Group", ""),
                        "class": doc.get("Class", ""),
                        "subclass": doc.get("Sub-Class", ""),
                        "similarity": similarity,
                        "similarity_percent": similarity_percent,
                        "description": doc.get("Description", doc.get("Sub-Class_Description", "No description available"))
                    }
                    formatted_results.append(result)
        else:
            # For English with MongoDB
            client, collection = get_mongodb_collection()
            raw_results = [(str(collection.find_one({"_id": ObjectId(idx)})["_id"]), 1.0 - float(distances[0][i])) 
                         for i, idx in enumerate(indices[0]) if idx >= 0]
            formatted_results = format_search_results(raw_results, collection)
            client.close()
        
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

@app.route('/api/languages', methods=['GET'])
def get_languages():
    return jsonify({"languages": SUPPORTED_LANGUAGES, "current": current_language})

@app.route('/api/set-language', methods=['POST'])
def set_language():
    data = request.get_json()
    language = data.get("language", DEFAULT_LANGUAGE).lower()
    
    global current_language
    if language in SUPPORTED_LANGUAGES:
        current_language = language
        return jsonify({"status": "success", "language": current_language})
    else:
        return jsonify({"status": "error", "message": f"Unsupported language: {language}"})

# Initialize language-specific data and indexes
def init_language_data():
    global language_data
    
    # Initialize English
    try:
        language_data["english"]["embedding_function"] = cached_get_embedding
        language_data["english"]["index"] = faiss_manager.index
        print("English language initialized successfully")
    except Exception as e:
        print(f"Error initializing English language support: {e}")
    
    # Initialize Hindi
    try:
        # First try to load pre-computed Hindi embeddings from output_hindi.json
        hindi_documents, hindi_embeddings_array, id_map = load_hindi_embeddings()
        
        if hindi_documents and len(hindi_documents) > 0 and hindi_embeddings_array is not None:
            # Create FAISS index for Hindi
            import faiss
            
            hindi_index_dimension = hindi_embeddings_array.shape[1]  # Get embedding dimension
            hindi_index = faiss.IndexFlatIP(hindi_index_dimension)   # Create index for inner product similarity
            if hindi_embeddings_array.shape[0] > 0:  # Make sure we have embeddings to add
                hindi_index.add(hindi_embeddings_array)              # Add embeddings to index
            
            # Store in language_data
            language_data["hindi"]["index"] = hindi_index
            language_data["hindi"]["embedding_function"] = get_hindi_embeddings
            language_data["hindi"]["documents"] = hindi_documents
            language_data["hindi"]["id_map"] = id_map
            
            print(f"Hindi language initialized with {len(hindi_documents)} documents from output_hindi.json")
        else:
            # Fallback to existing code if JSON loading fails
            language_data["hindi"]["embedding_function"] = get_hindi_embeddings
            import faiss
            try:
                hindi_index = faiss.read_index("hindi_faiss.index")
                language_data["hindi"]["index"] = hindi_index
                print("Hindi language index loaded from hindi_faiss.index")
            except:
                print("Hindi index not found, creating a new one")
                # Create an empty index for Hindi
                import faiss
                hindi_index = faiss.IndexFlatIP(768)  # Common embedding dimension
                language_data["hindi"]["index"] = hindi_index
    except Exception as e:
        print(f"Error initializing Hindi language support: {e}")

# Initialize language data when app starts
init_language_data()

@app.route('/hindi-search')
def hindi_search():
    """Render the Hindi search page"""
    return render_template('hindi_search.html')

if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs("Data Processing", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
