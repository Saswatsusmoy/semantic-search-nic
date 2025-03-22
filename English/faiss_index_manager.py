"""
FAISS Index Manager for semantic search
Handles building, saving, loading and querying the FAISS index
"""
import os
import time
import json
import logging
import traceback
import numpy as np
import faiss
from typing import List, Tuple, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default paths for index and ID map
DEFAULT_INDEX_PATH = "faiss_index.bin"
DEFAULT_ID_MAP_PATH = "faiss_id_map.json"
DEFAULT_JSON_PATH = "output.json"

class FAISSIndexManager:
    """Manages FAISS index operations for semantic search"""
    
    def __init__(self, 
                json_file_path: Optional[str] = None,
                index_path: Optional[str] = None, 
                id_map_path: Optional[str] = None):
        """
        Initialize the FAISS index manager
        
        Args:
            json_file_path: Path to the JSON data file
            index_path: Path to save/load the FAISS index
            id_map_path: Path to save/load the ID map
        """
        # Store paths
        self.index_path = index_path or DEFAULT_INDEX_PATH
        self.id_map_path = id_map_path or DEFAULT_ID_MAP_PATH
        self.json_file_path = json_file_path or DEFAULT_JSON_PATH
        
        # Initialize index and ID map
        self.index = None
        self.id_map = None
        
        logger.info(f"FAISS Index Manager initialized with json_file_path={self.json_file_path}, index_path={self.index_path}, id_map_path={self.id_map_path}")
    
    def load_json_data(self) -> List[Dict[str, Any]]:
        """
        Load data from the JSON file
        
        Returns:
            List of documents from the JSON file
        """
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            logger.info(f"Loaded {len(json_data)} documents from JSON file")
            return json_data
        except Exception as e:
            logger.error(f"Error loading JSON data: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def load_index(self) -> bool:
        """
        Load the FAISS index and ID map from disk
        
        Returns:
            bool: True if successfully loaded, False otherwise
        """
        try:
            # Check if the files exist
            if not os.path.exists(self.index_path) or not os.path.exists(self.id_map_path):
                logger.warning(f"Index or ID map file not found: {self.index_path} / {self.id_map_path}")
                return False
            
            # Load the index
            self.index = faiss.read_index(self.index_path)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors and dimension {self.index.d}")
            
            # Load the ID map
            with open(self.id_map_path, 'r') as f:
                # Convert string keys to integers, since JSON serializes all keys as strings
                id_map_raw = json.load(f)
                self.id_map = {int(k): v for k, v in id_map_raw.items()}
                
            logger.info(f"Loaded ID map with {len(self.id_map)} entries")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def build_index(self, force_rebuild: bool = False) -> bool:
        """
        Build or rebuild the FAISS index
        
        Args:
            force_rebuild: Force rebuild even if the index exists
            
        Returns:
            bool: True if successfully built, False otherwise
        """
        try:
            # Check if index already exists and we're not forcing a rebuild
            if not force_rebuild and self.index is not None:
                logger.info("Index already loaded, skipping build")
                return True
            
            # Check if files exist and we're not forcing a rebuild
            if not force_rebuild and os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
                logger.info("Index files exist, attempting to load instead of rebuild")
                return self.load_index()
            
            # Load data from JSON file
            json_data = self.load_json_data()
            if not json_data:
                logger.error("No data available to build index")
                return False
            
            logger.info(f"Building index from {len(json_data)} documents")
            
            # Extract document IDs and embeddings
            doc_ids = []
            embeddings = []
            
            for i, doc in enumerate(json_data):
                # Check if document has an embedding field
                embedding_field_name = "Vector-Embedding_SubClass"
                
                if embedding_field_name in doc and doc[embedding_field_name]:
                    # Get document ID and embedding
                    doc_id = str(doc["_id"])
                    embedding = doc[embedding_field_name]
                    
                    # Validate embedding
                    if isinstance(embedding, list) and len(embedding) > 0:
                        doc_ids.append(doc_id)
                        embeddings.append(embedding)
            
            if len(embeddings) == 0:
                logger.error("No valid embeddings found in data. Make sure the JSON contains 'Vector-Embedding_SubClass' fields.")
                return False
                
            logger.info(f"Found {len(embeddings)} valid embeddings out of {len(json_data)} documents")
                
            # Convert to numpy array
            embedding_matrix = np.array(embeddings).astype('float32')
            
            # Get dimensions
            num_vectors = embedding_matrix.shape[0]
            dimension = embedding_matrix.shape[1]
            
            logger.info(f"Building index with {num_vectors} vectors of dimension {dimension}")
            
            # Create inner product (cosine similarity) index
            # We normalize the vectors to use the inner product as cosine similarity
            faiss.normalize_L2(embedding_matrix)
            self.index = faiss.IndexFlatIP(dimension)
            
            # Add vectors to index with IDs
            self.index = faiss.IndexIDMap(self.index)
            ids_array = np.arange(num_vectors).astype('int64')
            self.index.add_with_ids(embedding_matrix, ids_array)
            
            # Create ID map
            self.id_map = {int(idx): doc_id for idx, doc_id in enumerate(doc_ids)}
            
            # Save the index and ID map
            faiss.write_index(self.index, self.index_path)
            with open(self.id_map_path, 'w') as f:
                json.dump(self.id_map, f)
            
            logger.info(f"Index built and saved successfully with {num_vectors} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Error building FAISS index: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Search the FAISS index with a query embedding
        
        Args:
            query_embedding: The query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of tuples (document_id, similarity_score)
        """
        try:
            # Ensure index is loaded
            if self.index is None:
                success = self.load_index()
                if not success:
                    logger.warning("Failed to load index, attempting to build it")
                    success = self.build_index()
                    if not success:
                        logger.error("Failed to build index")
                        return []
            
            if self.index.ntotal == 0:
                logger.warning("Index is empty (contains 0 vectors)")
                return []
            
            # Process the query embedding
            query_array = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_array)
            
            # Search the index
            D, I = self.index.search(query_array, min(top_k, self.index.ntotal))
            
            # Debug index search
            logger.debug(f"FAISS search returned {len(I[0])} results, top distances: {D[0][:5]}")
            
            results = []
            for idx, (distance, idx_val) in enumerate(zip(D[0], I[0])):
                # Skip invalid indices (-1 means no match found)
                if idx_val == -1:
                    continue
                    
                if idx_val in self.id_map:
                    doc_id = self.id_map[int(idx_val)]
                    # With cosine similarity, higher values are better (range: -1 to 1)
                    # A similarity of 1 means the vectors are identical
                    results.append((doc_id, float(distance)))
                else:
                    logger.warning(f"Index returned ID {idx_val} which is not in ID map")
            
            logger.info(f"Search completed with {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching FAISS index: {str(e)}")
            logger.error(traceback.format_exc())
            return []

# For command line usage
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build or test FAISS index")
    parser.add_argument("--build", action="store_true", help="Build the index")
    parser.add_argument("--test", action="store_true", help="Test the index")
    parser.add_argument("--force", action="store_true", help="Force rebuild index")
    parser.add_argument("--json", default=DEFAULT_JSON_PATH, help="Path to JSON data file")
    args = parser.parse_args()
    
    manager = FAISSIndexManager(json_file_path=args.json)
    
    if args.build:
        success = manager.build_index(force_rebuild=args.force)
        if success:
            print("Index built successfully")
        else:
            print("Failed to build index")
            
    if args.test:
        if not manager.load_index():
            print("Failed to load index")
        else:
            print(f"Loaded index with {manager.index.ntotal} vectors")
