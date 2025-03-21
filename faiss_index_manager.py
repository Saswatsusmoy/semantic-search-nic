"""
FAISS Index Manager for the NIC Codes Semantic Search Application
Handles creation, saving, and loading of FAISS indexes
Uses a hybrid approach with cosine similarity via inner product on normalized vectors
"""

import os
import faiss
import numpy as np
import pickle
from pymongo import MongoClient
import logging
from datetime import datetime
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FAISSIndexManager:
    def __init__(self, connection_string=None, database_name=None, collection_name=None):
        # Use provided values or fall back to environment variables
        self.connection_string = connection_string
        self.database_name = database_name or os.environ.get("DB_NAME", "NIC_Database")
        self.collection_name = collection_name or os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        self.index = None
        self.id_map = None  # Maps FAISS index positions to MongoDB document IDs
        self.index_path = os.path.join(os.path.dirname(__file__), "faiss_index")
        self.id_map_path = os.path.join(os.path.dirname(__file__), "faiss_id_map.pkl")
        self.json_file_path = os.path.join(os.path.dirname(__file__), "output.json")

    def connect_to_mongodb(self):
        """Connect to MongoDB and return the collection"""
        # For local JSON, we'll return a simple accessor class instead
        try:
            # Load JSON data
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            class LocalCollection:
                def __init__(self, data):
                    self.data = data
                    
                def find(self, query=None, projection=None):
                    results = []
                    for doc in self.data:
                        # Simple filtering for Vector-Embedding_SubClass exists query
                        if query and "$exists" in query.get("Vector-Embedding_SubClass", {}):
                            if "Vector-Embedding_SubClass" not in doc:
                                continue
                                
                        # Handle projection
                        if projection:
                            result = {}
                            include_doc = True
                            for field, include in projection.items():
                                if include and field in doc:
                                    result[field] = doc[field]
                                elif field == "_id" and include:
                                    # Ensure each document has an _id
                                    result["_id"] = doc.get("_id", str(hash(str(doc))))
                            if include_doc:
                                results.append(result)
                        else:
                            # Make sure each document has an _id
                            if "_id" not in doc:
                                doc["_id"] = str(hash(str(doc)))
                            results.append(doc)
                    return results
                    
            logger.info(f"Using local JSON data with {len(data)} documents")
            # Return None for client and the collection-like accessor
            return None, LocalCollection(data)
        except Exception as e:
            logger.error(f"Failed to load JSON data: {str(e)}")
            raise

    def normalize_vectors(self, vectors):
        """Normalize vectors for cosine similarity"""
        # Compute L2 norms
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Replace zero norms with tiny value to avoid division by zero
        norms[norms == 0] = 1e-10
        # Normalize
        return vectors / norms

    def build_index(self, force_rebuild=False):
        """
        Build a FAISS index from JSON file embeddings using cosine similarity
        
        Args:
            force_rebuild (bool): If True, rebuild the index even if it exists
            
        Returns:
            bool: True if index built successfully, False otherwise
        """
        # Check if index already exists
        if not force_rebuild and os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            logger.info("FAISS index already exists. Loading existing index...")
            return self.load_index()
        
        logger.info("Building new FAISS index with cosine similarity...")
        client = None
        try:
            client, collection = self.connect_to_mongodb()
            
            # Get all documents with vector embeddings
            query = {"Vector-Embedding_SubClass": {"$exists": True}}
            projection = {"_id": 1, "Vector-Embedding_SubClass": 1}
            
            # Get documents and extract embeddings
            documents = list(collection.find(query, projection))
            
            if not documents:
                logger.error("No documents with Vector-Embedding_SubClass found in JSON data")
                return False
                
            logger.info(f"Building index with {len(documents)} documents")
            
            # Extract document IDs and embeddings
            doc_ids = []
            embeddings = []
            
            for doc in documents:
                if "Vector-Embedding_SubClass" in doc and doc["Vector-Embedding_SubClass"]:
                    try:
                        # Handle both list and string representations
                        if isinstance(doc["Vector-Embedding_SubClass"], str):
                            # Parse string representation of list
                            embedding = json.loads(doc["Vector-Embedding_SubClass"].replace("'", '"'))
                        else:
                            embedding = doc["Vector-Embedding_SubClass"]
                            
                        # Ensure embedding is a list of floats
                        embedding = [float(x) for x in embedding]
                        
                        # Add to our lists
                        embeddings.append(embedding)
                        doc_ids.append(str(doc["_id"]))
                    except (ValueError, json.JSONDecodeError) as e:
                        logger.error(f"Error parsing embedding for document {doc['_id']}: {e}")
                        continue
            
            if not embeddings:
                logger.error("No valid embeddings found in documents")
                return False
                
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Normalize vectors for cosine similarity
            normalized_embeddings = self.normalize_vectors(embeddings_array)
            
            # Get dimensionality from the data
            d = normalized_embeddings.shape[1]
            
            # Create a FAISS index for inner product (cosine similarity with normalized vectors)
            self.index = faiss.IndexFlatIP(d)
            
            # Add vectors to the index
            self.index.add(normalized_embeddings)
            
            # Store mapping from index positions to document IDs
            self.id_map = doc_ids
            
            # Save the index and mapping to disk
            self.save_index()
            
            logger.info(f"FAISS index built successfully with {len(doc_ids)} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def save_index(self):
        """Save the FAISS index and ID mapping to disk"""
        try:
            if self.index is None or self.id_map is None:
                logger.error("Cannot save: Index or ID mapping is None")
                return False
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_path)
            
            # Save ID mapping
            with open(self.id_map_path, 'wb') as f:
                pickle.dump(self.id_map, f)
                
            logger.info(f"Saved FAISS index to {self.index_path} and ID mapping to {self.id_map_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            return False
    
    def load_index(self):
        """Load the FAISS index and ID mapping from disk"""
        try:
            if not os.path.exists(self.index_path) or not os.path.exists(self.id_map_path):
                logger.error("Index or ID mapping file not found")
                return False
                
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load ID mapping
            with open(self.id_map_path, 'rb') as f:
                self.id_map = pickle.load(f)
                
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            return False
    
    def search(self, query_embedding, top_k=10):
        """
        Search the FAISS index using cosine similarity
        
        Args:
            query_embedding (np.ndarray): The query embedding vector
            top_k (int): Number of results to return
            
        Returns:
            list: List of (doc_id, similarity) tuples
        """
        if self.index is None:
            logger.error("FAISS index not loaded")
            return []
            
        try:
            # Convert query to numpy array
            query_np = np.array([query_embedding]).astype('float32')
            
            # Normalize the query vector for cosine similarity
            query_np = self.normalize_vectors(query_np)
            
            # Search the index
            # For normalized vectors, inner product (IP) is equivalent to cosine similarity
            similarities, indices = self.index.search(query_np, top_k)
            
            # Map indices to MongoDB document IDs
            results = []
            for i, (idx, similarity) in enumerate(zip(indices[0], similarities[0])):
                if idx != -1 and idx in self.id_map:  # -1 indicates no match found
                    doc_id = self.id_map[idx]
                    # With cosine similarity, higher values are better (range: -1 to 1)
                    # A similarity of 1 means the vectors are identical
                    results.append((doc_id, float(similarity)))
            
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {str(e)}")
            return []

# Utility function to create/update index
def create_or_update_index(connection_string, force_rebuild=False):
    """Create or update the FAISS index"""
    manager = FAISSIndexManager(connection_string)
    success = manager.build_index(force_rebuild)
    return success

if __name__ == "__main__":
    # Example usage
    connection_string = "mongodb+srv://saswatsusmoy8013:12345@cluster1.onj53.mongodb.net/"
    
    # Create or update index
    create_or_update_index(connection_string, force_rebuild=True)
    
    logger.info("Index creation complete")
