"""
Script to verify the structure of the JSON data file and check for required fields
"""
import os
import json
import logging
import argparse
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_json_data(json_path="output.json", sample_count=5, fix=False):
    """
    Verify that JSON data contains required fields and valid embeddings
    
    Args:
        json_path: Path to the JSON file
        sample_count: Number of sample documents to display
        fix: Whether to attempt to convert certain fields if they're not in the right format
    """
    try:
        # Check if file exists
        if not os.path.exists(json_path):
            logger.error(f"JSON file not found: {json_path}")
            return False
            
        # Load the file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.info(f"Loaded JSON file with {len(data)} documents")
        
        if not isinstance(data, list):
            logger.error(f"JSON data is not a list (found {type(data).__name__})")
            return False
            
        if len(data) == 0:
            logger.error("JSON data is empty")
            return False
            
        # Check for required fields
        required_fields = ["_id", "Vector-Embedding_SubClass"]
        
        # Statistics
        stats = {
            "total": len(data),
            "with_embedding": 0,
            "missing_embedding": 0,
            "invalid_embedding": 0,
            "fixed_embeddings": 0
        }
        
        logger.info(f"Checking {len(data)} documents for required fields: {', '.join(required_fields)}")
        
        # Verify each document
        fixed_data = []
        for i, doc in enumerate(data):
            fixed_doc = doc.copy()
            missing_fields = [field for field in required_fields if field not in doc]
            
            if missing_fields:
                if i < sample_count:
                    logger.warning(f"Document at index {i} is missing fields: {', '.join(missing_fields)}")
                stats["missing_embedding"] += 1
            elif "Vector-Embedding_SubClass" in doc:
                embedding = doc["Vector-Embedding_SubClass"]
                
                if embedding is None:
                    stats["missing_embedding"] += 1
                    if i < sample_count:
                        logger.warning(f"Document at index {i} has None embedding")
                    continue
                    
                # Check if embedding is a valid list or array
                if isinstance(embedding, list) and len(embedding) > 0:
                    try:
                        # Try converting to numpy array to validate
                        np_embedding = np.array(embedding)
                        if np_embedding.ndim != 1:
                            logger.warning(f"Document at index {i} has incorrect embedding shape: {np_embedding.shape}")
                            stats["invalid_embedding"] += 1
                        else:
                            stats["with_embedding"] += 1
                    except:
                        logger.warning(f"Document at index {i} has invalid embedding format")
                        stats["invalid_embedding"] += 1
                else:
                    stats["invalid_embedding"] += 1
                    if i < sample_count:
                        logger.warning(f"Document at index {i} has invalid embedding format: {type(embedding).__name__}")
            
            fixed_data.append(fixed_doc)
                    
        # Report statistics
        logger.info(f"Statistics:")
        logger.info(f"- Total documents: {stats['total']}")
        logger.info(f"- Documents with valid embeddings: {stats['with_embedding']} ({stats['with_embedding']/stats['total']*100:.2f}%)")
        logger.info(f"- Documents with missing embeddings: {stats['missing_embedding']} ({stats['missing_embedding']/stats['total']*100:.2f}%)")
        logger.info(f"- Documents with invalid embeddings: {stats['invalid_embedding']} ({stats['invalid_embedding']/stats['total']*100:.2f}%)")
        logger.info(f"- Fixed embeddings: {stats['fixed_embeddings']}")
        
        # Show sample document
        if len(data) > 0:
            logger.info("\nSample document fields:")
            sample_doc = data[0]
            for key, value in sample_doc.items():
                value_str = str(value)
                if key == "Vector-Embedding_SubClass" and isinstance(value, list):
                    value_str = f"[{value[0]:.6f}, {value[1]:.6f}, ... {len(value)} values]"
                logger.info(f"- {key}: {value_str}")
        
        # Save fixed data if needed
        if fix and stats["fixed_embeddings"] > 0:
            fixed_path = Path(json_path).with_suffix(".fixed.json")
            with open(fixed_path, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved fixed data to {fixed_path}")
            
        # Return success based on whether we found valid embeddings
        return stats["with_embedding"] > 0
        
    except Exception as e:
        logger.error(f"Error verifying JSON data: {str(e)}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="Verify JSON data for search application")
    parser.add_argument("--path", "-p", default="output.json", help="Path to JSON file")
    parser.add_argument("--samples", "-s", type=int, default=5, help="Number of sample documents to show")
    parser.add_argument("--fix", "-f", action="store_true", help="Fix issues if possible")
    
    args = parser.parse_args()
    
    success = verify_json_data(args.path, args.samples, args.fix)
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
