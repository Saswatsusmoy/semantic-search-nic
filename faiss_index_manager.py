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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FAISSIndexManager:
    def __init__(self, connection_string=None, database_name=None, collection_name=None):
        # Use provided values or fall back to environment variables
        self.connection_string = connection_string or os.environ.get("MONGO_URI")
        self.database_name = database_name or os.environ.get("DB_NAME", "NIC_Database")
        self.collection_name = collection_name or os.environ.get("COLLECTION_NAME", "NIC_Codes")
        
        self.index = None
        self.id_map = None  # Maps FAISS index positions to MongoDB document IDs
        self.index_path = os.path.join(os.path.dirname(__file__), "faiss_index")
        self.id_map_path = os.path.join(os.path.dirname(__file__), "faiss_id_map.pkl")
    
    def connect_to_mongodb(self):
        """Connect to MongoDB and return the collection"""
        try:
            if not self.connection_string:
                raise ValueError("MongoDB connection string not provided and not found in environment variables")
                
            client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            db = client[self.database_name]
            collection = db[self.collection_name]
            return client, collection
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    
    def normalize_vectors(self, vectors):
        """
        Normalize vectors to unit length for cosine similarity
        
        Args:
            vectors (np.ndarray): Vectors to normalize
            
        Returns:
            np.ndarray: Normalized vectors
        """
        # Calculate the L2 norm of each vector
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms = np.maximum(norms, 1e-10)
        # Normalize each vector to have unit length
        normalized_vectors = vectors / norms
        return normalized_vectors
    
    def build_index(self, force_rebuild=False):
        """
        Build a FAISS index from MongoDB embeddings using cosine similarity
        
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
            logger.info(f"Found {len(documents)} documents with embeddings")
            
            if not documents:
                logger.error("No documents found with embeddings")
                return False
            
            # Extract embeddings and document IDs
            embeddings = []
            doc_ids = []
            
            for doc in documents:
                if "Vector-Embedding_SubClass" in doc and isinstance(doc["Vector-Embedding_SubClass"], list):
                    embeddings.append(doc["Vector-Embedding_SubClass"])
                    doc_ids.append(str(doc["_id"]))
            
            if not embeddings:
                logger.error("No valid embeddings found in documents")
                return False
                
            # Convert to numpy array
            embeddings_array = np.array(embeddings).astype('float32')
            
            # Normalize vectors for cosine similarity
            normalized_embeddings = self.normalize_vectors(embeddings_array)
            logger.info(f"Normalized {len(normalized_embeddings)} vectors for cosine similarity")
            
            # Get embedding dimension
            dimension = normalized_embeddings.shape[1]
            logger.info(f"Building index with {len(normalized_embeddings)} vectors of dimension {dimension}")
            
            # Create FAISS index for cosine similarity (inner product on normalized vectors)
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            self.index = faiss.IndexIDMap(self.index)
            
            # Generate sequential IDs for the index
            ids = np.arange(len(normalized_embeddings), dtype=np.int64)
            
            # Add vectors to the index
            self.index.add_with_ids(normalized_embeddings, ids)
            
            # Create ID mapping (FAISS index position -> MongoDB document ID)
            self.id_map = {int(idx): doc_id for idx, doc_id in enumerate(doc_ids)}
            
            logger.info(f"Built FAISS index with {self.index.ntotal} vectors using cosine similarity")
            
            # Save the index and ID mapping
            return self.save_index()
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}")
            return False
        finally:
            if client:
                client.close()
    
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
