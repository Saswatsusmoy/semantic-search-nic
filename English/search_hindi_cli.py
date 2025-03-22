#!/usr/bin/env python3
"""
Command-line interface for Hindi semantic search
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any
import time
from hindi_semantic_search import HindiSemanticSearch

def format_result_text(result: Dict[str, Any]) -> str:
    """Format a search result for text display"""
    doc = result["document"]
    score_percent = round(result["score"] * 100)
    
    output = []
    output.append(f"[{result['rank']}] Score: {score_percent}% - {doc['description']}")
    
    # Add classification details
    if doc.get("section"):
        output.append(f"    Section: {doc['section']}")
    if doc.get("division"):
        output.append(f"    Division: {doc['division']}")
    if doc.get("group"):
        output.append(f"    Group: {doc['group']}")
    if doc.get("class"):
        output.append(f"    Class: {doc['class']}")
    if doc.get("subclass"):
        output.append(f"    Subclass: {doc['subclass']}")
    
    return "\n".join(output)

def print_results(results: List[Dict[str, Any]], json_output: bool = False) -> None:
    """Print search results in the specified format"""
    if json_output:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No results found.")
            return
            
        print(f"\nFound {len(results)} results:\n")
        for result in results:
            print(format_result_text(result))
            print("-" * 80)

def interactive_search(search_engine: HindiSemanticSearch) -> None:
    """Run an interactive search session"""
    print("\n=== हिंदी सिमैंटिक सर्च इंटरैक्टिव मोड ===\n")
    print("Type your search queries in Hindi. Type 'exit' or press Ctrl+C to quit.\n")
    
    while True:
        try:
            query = input("\nSearch query > ")
            if query.lower() in ('exit', 'quit', 'q'):
                break
                
            if not query.strip():
                continue
                
            print("Searching...")
            start_time = time.time()
            results = search_engine.search(query, top_k=5)
            elapsed = time.time() - start_time
            
            print(f"\nSearch completed in {elapsed:.3f} seconds.")
            print_results(results)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Hindi Semantic Search using FAISS")
    
    # Query argument (optional for build-index or interactive mode)
    parser.add_argument("query", nargs="?", help="Search query in Hindi")
    
    # Index options
    parser.add_argument("--build-index", action="store_true", help="Build and save the FAISS index")
    parser.add_argument("--index", default="hindi_faiss.index", help="Path to FAISS index file")
    parser.add_argument("--embeddings-file", default="output_hindi.json", help="Path to embeddings JSON file")
    
    # Search options
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    try:
        # Initialize search engine
        if args.build_index:
            # For building index, use the embeddings file
            search_engine = HindiSemanticSearch(embeddings_file=args.embeddings_file)
            if search_engine.index:
                success = search_engine.save_index(args.index)
                if success:
                    print(f"Index successfully built and saved to {args.index}")
                    stats = search_engine.get_index_stats()
                    print(f"Index stats: {stats}")
                return 0 if success else 1
            return 1
        else:
            # For searching, try to load existing index first
            if os.path.exists(args.index):
                search_engine = HindiSemanticSearch(index_path=args.index, embeddings_file=None)
            else:
                # Fall back to building from embeddings
                print(f"Index not found at {args.index}, loading from embeddings file")
                search_engine = HindiSemanticSearch(embeddings_file=args.embeddings_file)
        
        # If no query provided, enter interactive mode
        if not args.query:
            interactive_search(search_engine)
            return 0
        
        # Otherwise, perform search with the provided query
        start_time = time.time()
        results = search_engine.search(args.query, top_k=args.top_k)
        elapsed = time.time() - start_time
        
        if not args.json:
            print(f"Search completed in {elapsed:.3f} seconds.")
        
        print_results(results, args.json)
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation interrupted.")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
