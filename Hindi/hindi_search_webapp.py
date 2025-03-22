#!/usr/bin/env python3
"""
Web application for Hindi semantic search
"""

import os
import json
import time
import math
import numpy as np
from flask import Flask, render_template, request, jsonify
from hindi_semantic_search import HindiSemanticSearch
from recording import start_recording, stop_recording

# Create a custom JSONEncoder to handle NaN values properly
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            if math.isnan(obj) or math.isinf(obj):
                return str(obj)  # Convert NaN/Infinity to string representation
            return float(obj)
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        return super().default(obj)

app = Flask(__name__, template_folder='templates', static_folder='static')
# Set the custom JSON encoder for the Flask app
app.json_encoder = CustomJSONEncoder

# Global search engine instance
search_engine = None

def initialize_search_engine():
    """Initialize the search engine with the index"""
    global search_engine
    
    index_path = "hindi_faiss.index"
    embeddings_file = "output_hindi.json"
    
    # Try to load existing index first
    if os.path.exists(index_path):
        search_engine = HindiSemanticSearch(index_path=index_path, embeddings_file=None)
    else:
        # Fall back to building from embeddings
        print(f"Index not found at {index_path}, loading from embeddings file")
        search_engine = HindiSemanticSearch(embeddings_file=embeddings_file)
    
    return search_engine is not None

@app.route('/')
def index():
    """Render the main search page"""
    # Get index stats to display on the homepage
    stats = {}
    if search_engine:
        stats = search_engine.get_index_stats()
    
    # Add app information for the template
    app_info = {
        "app_name": "Hindi Semantic Search",
        "version": "2.0.0",
        "description": "Advanced semantic search for Hindi text using FAISS and transformer models",
        "year": time.strftime("%Y")
    }
    
    return render_template('index.html', stats=stats, app_info=app_info)

@app.route('/search', methods=['POST'])
def search():
    """Handle search query and return results"""
    try:
        # Get query from request
        query = request.form.get('query', '')
        top_k = int(request.form.get('top_k', 5))
        
        if not query.strip():
            return jsonify({"error": "Empty query", "results": []})
        
        # Perform search
        start_time = time.time()
        results = search_engine.search(query, top_k=top_k)
        elapsed = time.time() - start_time
        
        # Process the results to handle any problematic values
        processed_results = []
        for result in results:
            # Create a clean copy of the result
            processed_result = {
                "rank": result.get("rank"),
                "score": result.get("score"),
                "document": {}
            }
            
            # Process document fields to ensure JSON compatibility
            if "document" in result:
                doc = result["document"]
                for key, value in doc.items():
                    # Convert NaN to string representation for clean JSON serialization
                    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                        processed_result["document"][key] = str(value)
                    else:
                        processed_result["document"][key] = value
            
            processed_results.append(processed_result)
        
        # Return results and stats using custom JSON encoder
        response_data = {
            "results": processed_results,
            "elapsed": round(elapsed, 3),
            "count": len(processed_results),
            "query": query
        }
        
        # Manual JSON validation to catch any serialization issues early
        try:
            # Test serialization
            json.dumps(response_data, cls=CustomJSONEncoder)
        except TypeError as e:
            print(f"JSON serialization error: {str(e)}")
            return jsonify({"error": "Server could not serialize response data", "results": []})
            
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error processing search: {str(e)}")
        return jsonify({"error": str(e), "results": []})

# Add environment flag for server environments without audio capture capability
import os
SERVER_ENV = os.environ.get('SERVER_ENV', '').lower()
DISABLE_AUDIO = SERVER_ENV in ('production', 'staging', 'docker') or os.environ.get('DISABLE_AUDIO') == '1'

@app.route('/api/start_recording', methods=['POST'])
def start_recording_endpoint():
    """API endpoint to start audio recording"""
    try:
        # Check if audio is disabled in this environment
        if DISABLE_AUDIO:
            print("Audio recording disabled on this server. Using simulation mode.")
            # Use simulation mode when audio is disabled
            success, message = start_recording(device_id=None, use_simulation=True)
        else:
            # Get device ID if provided in the request - with safer JSON handling
            device_id = None
            if request.is_json and request.get_json(silent=True):
                device_id = request.json.get('device_id')
            
            # Start recording with comprehensive error handling
            success, message = start_recording(device_id)
        
        if success:
            return jsonify({"status": "success", "message": "Recording started"})
        else:
            print(f"Failed to start recording: {message}")
            return jsonify({"status": "error", "message": message}), 500
    except Exception as e:
        import traceback
        error_message = f"Server error starting recording: {str(e)}"
        traceback.print_exc()  # Print full traceback to server logs
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500

@app.route('/api/stop_recording', methods=['POST'])
def stop_recording_endpoint():
    """API endpoint to stop recording and get transcription"""
    try:
        # Create directory if it doesn't exist
        os.makedirs("Data Processing", exist_ok=True)
        output_filename = "Data Processing/output.wav"
        transcript = stop_recording(output_filename)
        
        # Use transcript as search query if available
        if transcript and transcript not in ["Speech unclear", "Error: Audio file not found", 
                                           "No audio data recorded", "No active recording session"]:
            return jsonify({
                "status": "success", 
                "message": "Recording stopped", 
                "transcript": transcript
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Failed to transcribe audio", 
                "transcript": transcript or "Unknown error"
            })
    except Exception as e:
        error_message = f"Server error stopping recording: {str(e)}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500

# Add new diagnostic endpoint
@app.route('/api/audio_devices', methods=['GET'])
def list_audio_devices_endpoint():
    """List available audio devices for troubleshooting"""
    try:
        from recording import list_audio_devices
        devices = list_audio_devices()
        
        device_list = []
        for i, device in enumerate(devices):
            device_list.append({
                "id": i,
                "name": device['name'],
                "inputs": device['max_input_channels'],
                "outputs": device['max_output_channels'],
                "default_input": device.get('default_input', False),
                "default_output": device.get('default_output', False)
            })
            
        return jsonify({
            "status": "success",
            "devices": device_list
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/system_info', methods=['GET'])
def system_info_endpoint():
    """Return information about the server environment and audio capabilities"""
    try:
        from recording import list_audio_devices
        import platform
        
        # Get audio devices
        devices = list_audio_devices()
        device_list = []
        
        for i, device in enumerate(devices):
            device_list.append({
                "id": i,
                "name": device.get('name', 'Unknown'),
                "inputs": device.get('max_input_channels', 0),
                "outputs": device.get('max_output_channels', 0),
                "default_input": device.get('default_input', False),
                "default_output": device.get('default_output', False)
            })
        
        # System information
        sys_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "simulation_mode": DISABLE_AUDIO,
            "server_env": SERVER_ENV,
            "can_record": len(device_list) > 0 and not DISABLE_AUDIO,
            "devices": device_list
        }
        
        return jsonify({
            "status": "success",
            "system_info": sys_info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/get-index-stats')
def get_index_stats():
    """Return FAISS index statistics"""
    if not search_engine:
        return jsonify({"error": "Search engine not initialized"})
    
    stats = search_engine.get_index_stats()
    return jsonify(stats)

if __name__ == "__main__":
    if initialize_search_engine():
        print("Search engine initialized successfully. Starting web server...")
        app.run(debug=True, host='0.0.0.0', port=5500)
    else:
        print("Failed to initialize search engine.")
