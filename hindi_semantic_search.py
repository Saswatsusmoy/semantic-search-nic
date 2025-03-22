"""
Hindi Semantic Search implementation using FAISS and pre-computed embeddings
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Union, Tuple
import torch
from transformers import AutoTokenizer, AutoModel

class HindiSemanticSearch:
    """
    Semantic search for Hindi documents using FAISS
    """
    def __init__(self, 
                 embeddings_file: Optional[str] = "output_hindi.json",
                 index_path: Optional[str] = None,
                 model_name: str = "krutrim-ai-labs/Vyakyarth"):
        """
        Initialize Hindi semantic search
        
        Args:
            embeddings_file: Path to the JSON file containing pre-computed embeddings
            index_path: Path to a pre-built FAISS index file
            model_name: The embedding model to use for query encoding
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.documents = []
        self.index = None
        self.id_map = {}
        
        if index_path and os.path.exists(index_path):
            self.load_index(index_path)
        elif embeddings_file:
            self.load_embeddings(embeddings_file)
        else:
            raise ValueError("Either embeddings_file or index_path must be provided")
    
    def load_embeddings(self, embeddings_file: str) -> bool:
        """
        Load embeddings from JSON file and build the FAISS index
        
        Args:
            embeddings_file: Path to the JSON file with embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(embeddings_file):
            print(f"Error: Embeddings file not found at {embeddings_file}")
            return False
        
        print(f"Loading Hindi embeddings from {embeddings_file}")
        try:
            with open(embeddings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract documents with embeddings
            embeddings_list = []
            valid_docs = []
            
            for idx, doc in enumerate(data):
                if "embeddings" in doc and doc["embeddings"]:
                    # Store the document
                    valid_docs.append(doc)
                    # Store the embedding
                    embeddings_list.append(doc["embeddings"])
                    # Create a mapping from FAISS index to document ID
                    self.id_map[len(self.id_map)] = str(doc.get("_id", idx))
            
            print(f"Loaded {len(valid_docs)} documents with valid embeddings")
            if len(valid_docs) == 0:
                print("Error: No valid embeddings found in the file")
                return False
            
            # Store documents for later retrieval
            self.documents = valid_docs
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings_list, dtype=np.float32)
            
            # Get dimension from the embeddings
            dimension = embeddings_array.shape[1]
            
            # Create and fill the index
            # Using IndexFlatIP for inner product (cosine similarity on normalized vectors)
            self.index = faiss.IndexFlatIP(dimension)
            
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Add vectors to the index
            self.index.add(embeddings_array)
            
            print(f"FAISS index built with {self.index.ntotal} vectors of dimension {dimension}")
            return True
            
        except Exception as e:
            print(f"Error loading embeddings: {str(e)}")
            return False
    
    def load_index(self, index_path: str) -> bool:
        """
        Load a pre-built FAISS index
        
        Args:
            index_path: Path to the FAISS index file
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(index_path):
            print(f"Error: Index file not found at {index_path}")
            return False
        
        try:
            print(f"Loading FAISS index from {index_path}")
            self.index = faiss.read_index(index_path)
            print(f"Loaded FAISS index with {self.index.ntotal} vectors")
            
            # If we don't have documents loaded, try to load embeddings file to get documents
            if not self.documents and os.path.exists("output_hindi.json"):
                with open("output_hindi.json", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.documents = [doc for doc in data if "embeddings" in doc and doc["embeddings"]]
                # Rebuild id_map
                for idx, doc in enumerate(self.documents):
                    self.id_map[idx] = str(doc.get("_id", idx))
                    
            return True
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            return False
    
    def save_index(self, index_path: str) -> bool:
        """
        Save the FAISS index to a file
        
        Args:
            index_path: Path to save the index
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.index is None:
            print("Error: No index to save")
            return False
        
        try:
            print(f"Saving FAISS index to {index_path}")
            faiss.write_index(self.index, index_path)
            print(f"Index saved successfully to {index_path}")
            return True
        except Exception as e:
            print(f"Error saving index: {str(e)}")
            return False
    
    def _load_model(self):
        """Load the transformer model for encoding queries"""
        if self.tokenizer is None or self.model is None:
            try:
                print(f"Loading Hindi embedding model: {self.model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                self.model.eval()
                print("Model loaded successfully")
            except Exception as e:
                print(f"Error loading model: {str(e)}")
                return False
        return True
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query into an embedding vector
        
        Args:
            query: The search query text
            
        Returns:
            np.ndarray: The embedding vector
        """
        if not self._load_model():
            return None
        
        try:
            # Preprocess query (remove extra spaces)
            query = ' '.join(query.split())
            
            # Tokenize and encode
            with torch.no_grad():
                inputs = self.tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=512)
                outputs = self.model(**inputs)
                
                # Get the last hidden state
                last_hidden_state = outputs.last_hidden_state
                
                # Get attention mask to avoid padding tokens
                attention_mask = inputs['attention_mask']
                
                # Apply attention mask to last hidden state
                input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
                
                # Sum the masked hidden state
                sum_embeddings = torch.sum(last_hidden_state * input_mask_expanded, 1)
                sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
                
                # Get the mean pooled vector
                embedding = (sum_embeddings / sum_mask).squeeze().numpy()
                
                # Reshape for FAISS if needed
                if len(embedding.shape) == 1:
                    embedding = embedding.reshape(1, -1)
                
                # Normalize for cosine similarity
                faiss.normalize_L2(embedding)
                
                return embedding
                
        except Exception as e:
            print(f"Error encoding query: {str(e)}")
            return None
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for documents similar to the query
        
        Args:
            query: The search query
            top_k: Number of results to return
            
        Returns:
            List[Dict]: List of search results
        """
        if self.index is None:
            print("Error: No index loaded")
            return []
        
        # Encode the query
        query_vector = self.encode_query(query)
        if query_vector is None:
            return []
        
        # Search the index
        try:
            # Limit top_k to index size
            effective_top_k = min(top_k, self.index.ntotal)
            
            # Search using cosine similarity
            distances, indices = self.index.search(query_vector, effective_top_k)
            
            # Format results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0:  # Skip invalid indices
                    continue
                    
                # Convert FAISS index to document ID using id_map
                doc_id = self.id_map.get(int(idx))
                if doc_id is None:
                    continue
                
                # Find the document with this ID
                doc = None
                for document in self.documents:
                    if str(document.get("_id")) == doc_id:
                        doc = document
                        break
                
                if doc:
                    # Format the result
                    result = {
                        "rank": i + 1,
                        "score": float(distance),  # Cosine similarity score (higher is better)
                        "document": {
                            "id": doc_id,
                            "description": doc.get("Description", "No description"),
                            "section": doc.get("Section", ""),
                            "division": doc.get("Divison", ""),  # Note: Typo in the original data
                            "group": doc.get("Group", ""),
                            "class": doc.get("Class", ""),
                            "subclass": doc.get("Sub-Class", "")
                        }
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Error performing search: {str(e)}")
            return []
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the FAISS index
        
        Returns:
            Dict: Index statistics
        """
        if self.index is None:
            return {"error": "No index loaded"}
        
        return {
            "vector_count": self.index.ntotal,
            "dimension": self.index.d if hasattr(self.index, 'd') else "Unknown",
            "document_count": len(self.documents),
            "id_map_size": len(self.id_map)
        }
