"""
Vector Embeddings Manager for the NIC Codes Semantic Search Application
Handles generation, caching, and optimization of text embeddings
"""

import numpy as np
import os
import pickle
import time
import hashlib
from typing import List, Dict, Any, Union, Optional
import logging
from sentence_transformers import SentenceTransformer
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VectorEmbeddingsManager:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', cache_dir: str = 'embedding_cache'):
        """
        Initialize the embeddings manager with model and caching
        
        Args:
            model_name: The sentence-transformers model to use
            cache_dir: Directory to store embedding cache
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self._model = None  # Lazy loading
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache from disk
        self.cache_file = os.path.join(cache_dir, f"{model_name.replace('/', '_')}_cache.pkl")
        self.embedding_cache = self._load_cache()
        
        # Stats
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_embedding_time = 0
        
        logger.info(f"Initialized Vector Embeddings Manager with model '{model_name}'")
    
    @property
    def model(self):
        """Lazy load the model only when needed"""
        if self._model is None:
            start_time = time.time()
            logger.info(f"Loading embedding model '{self.model_name}'...")
            self._model = SentenceTransformer(self.model_name)
            logger.info(f"Model loaded in {time.time() - start_time:.2f} seconds")
        return self._model
    
    def _get_cache_key(self, text: str) -> str:
        """Generate a unique cache key for text"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _load_cache(self) -> Dict[str, np.ndarray]:
        """Load embedding cache from disk"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                logger.info(f"Loaded embedding cache with {len(cache)} entries")
                return cache
        except Exception as e:
            logger.warning(f"Error loading embedding cache: {str(e)}")
        
        return {}
    
    def _save_cache(self) -> None:
        """Save embedding cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.embedding_cache, f)
            logger.info(f"Saved {len(self.embedding_cache)} entries to embedding cache")
        except Exception as e:
            logger.warning(f"Error saving embedding cache: {str(e)}")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for a single text input with caching
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            numpy array of embedding vector
        """
        if not text or not isinstance(text, str):
            logger.warning(f"Invalid text input: {text}")
            # Return zero vector with correct dimensions as fallback
            if self._model is not None:
                return np.zeros(self.model.get_sentence_embedding_dimension(), dtype=np.float32)
            else:
                return np.zeros(384, dtype=np.float32)  # Default dimension for all-MiniLM-L6-v2
        
        # Check cache
        cache_key = self._get_cache_key(text)
        if cache_key in self.embedding_cache:
            self.cache_hits += 1
            return self.embedding_cache[cache_key]
        
        # Cache miss - generate embedding
        self.cache_misses += 1
        start_time = time.time()
        embedding = self.model.encode(text, show_progress_bar=False, convert_to_numpy=True)
        self.total_embedding_time += time.time() - start_time
        
        # Update cache
        self.embedding_cache[cache_key] = embedding
        
        # Periodically save cache to disk (every 100 new embeddings)
        if self.cache_misses % 100 == 0:
            self._save_cache()
        
        return embedding
    
    def get_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Get embeddings for a batch of texts with efficient batching and caching
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Size of batches for processing
            
        Returns:
            List of numpy arrays with embeddings
        """
        results = []
        texts_to_embed = []
        indices_to_embed = []
        
        # Check cache first for all texts
        for i, text in enumerate(texts):
            if not text or not isinstance(text, str):
                # Handle invalid inputs
                if self._model is not None:
                    results.append(np.zeros(self.model.get_sentence_embedding_dimension(), dtype=np.float32))
                else:
                    results.append(np.zeros(384, dtype=np.float32))
                continue
                
            cache_key = self._get_cache_key(text)
            if cache_key in self.embedding_cache:
                self.cache_hits += 1
                results.append(self.embedding_cache[cache_key])
            else:
                # Mark for embedding
                results.append(None)  # Placeholder
                texts_to_embed.append(text)
                indices_to_embed.append(i)
        
        # Process texts not in cache in batches
        if texts_to_embed:
            self.cache_misses += len(texts_to_embed)
            
            # Process in batches for efficiency
            for i in range(0, len(texts_to_embed), batch_size):
                batch_texts = texts_to_embed[i:i+batch_size]
                batch_indices = indices_to_embed[i:i+batch_size]
                
                start_time = time.time()
                batch_embeddings = self.model.encode(batch_texts, show_progress_bar=False, convert_to_numpy=True)
                self.total_embedding_time += time.time() - start_time
                
                # Update results and cache
                for j, (idx, embedding) in enumerate(zip(batch_indices, batch_embeddings)):
                    results[idx] = embedding
                    cache_key = self._get_cache_key(texts_to_embed[i+j])
                    self.embedding_cache[cache_key] = embedding
            
            # Save cache if we processed new embeddings
            self._save_cache()
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding cache and performance"""
        return {
            "cache_size": len(self.embedding_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "total_requests": self.cache_hits + self.cache_misses,
            "total_embedding_time": self.total_embedding_time
        }
    
    def clear_cache(self) -> None:
        """Clear the embedding cache"""
        self.embedding_cache = {}
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        logger.info("Embedding cache cleared")
    
    def change_model(self, new_model_name: str) -> bool:
        """
        Change the embedding model
        
        Args:
            new_model_name: Name of the new model to use
            
        Returns:
            bool: True if model changed successfully, False otherwise
        """
        try:
            # Save current cache if different model
            if new_model_name != self.model_name:
                self._save_cache()
                
                # Update model name and path
                self.model_name = new_model_name
                self.cache_file = os.path.join(self.cache_dir, f"{new_model_name.replace('/', '_')}_cache.pkl")
                
                # Unload current model and load new cache
                self._model = None
                self.embedding_cache = self._load_cache()
                
                # Reset stats
                self.cache_hits = 0
                self.cache_misses = 0
                self.total_embedding_time = 0
                
                logger.info(f"Changed model to '{new_model_name}'")
            
            return True
        except Exception as e:
            logger.error(f"Error changing model: {str(e)}")
            return False

# Singleton instance for application-wide use
embeddings_manager = None

def get_embeddings_manager(model_name: str = 'all-MiniLM-L6-v2') -> VectorEmbeddingsManager:
    """Get the singleton instance of the embeddings manager"""
    global embeddings_manager
    if embeddings_manager is None:
        embeddings_manager = VectorEmbeddingsManager(model_name=model_name)
    return embeddings_manager

# Cached version of get_embedding for repeated queries
@lru_cache(maxsize=1024)
def cached_get_embedding(text: str, model_name: str = 'all-MiniLM-L6-v2') -> np.ndarray:
    """Memory-efficient cached version of get_embedding"""
    manager = get_embeddings_manager(model_name)
    return manager.get_embedding(text)

if __name__ == "__main__":
    # Example usage
    manager = VectorEmbeddingsManager()
    
    # Test single embedding
    start = time.time()
    embedding = manager.get_embedding("This is a test sentence for embedding.")
    print(f"Single embedding time: {time.time() - start:.4f}s, shape: {embedding.shape}")
    
    # Test batch embedding
    test_texts = [
        "Manufacturing of textiles",
        "Software development services",
        "Restaurant and catering activities",
        "Agricultural production",
        "This is a test sentence for embedding."  # Should use cache
    ]
    
    start = time.time()
    batch_embeddings = manager.get_embeddings_batch(test_texts)
    print(f"Batch embedding time: {time.time() - start:.4f}s for {len(test_texts)} texts")
    
    # Print stats
    print("Embedding Manager Stats:", manager.get_stats())
