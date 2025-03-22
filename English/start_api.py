"""
Script to start the FastAPI application with Uvicorn server
"""

import uvicorn
import argparse
import os
import sys
import traceback

def main():
    parser = argparse.ArgumentParser(description='Start the NIC Code Semantic Search API')
    parser.add_argument('--host', default='0.0.0.0', help='Host IP (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Port (default: 8000)')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload for development')
    parser.add_argument('--workers', type=int, default=1, help='Number of worker processes (default: 1)')
    parser.add_argument('--log-level', default='info', 
                      choices=['debug', 'info', 'warning', 'error', 'critical'], 
                      help='Log level (default: info)')
    parser.add_argument('--no-checks', action='store_true', 
                      help='Skip directory checks (use if running from a different directory)')
    
    args = parser.parse_args()
    
    # Check if API module exists
    if not os.path.exists("api.py") and not args.no_checks:
        print("Error: 'api.py' not found in the current directory")
        print(f"Current directory: {os.getcwd()}")
        print("Make sure you're running this script from the project root directory")
        print("Or use --no-checks to skip this check")
        return 1
    
    # Check if static directory exists
    if not os.path.exists("static") and not args.no_checks:
        print("Warning: 'static' directory not found. Static files will not be available.")
    
    print(f"Starting NIC Code Semantic Search API on {args.host}:{args.port}")
    print(f"API and interactive documentation available at http://{args.host if args.host != '0.0.0.0' else '127.0.0.1'}:{args.port}/")
    print(f"Alternative API docs available at http://{args.host if args.host != '0.0.0.0' else '127.0.0.1'}:{args.port}/redoc")
    print("The FastAPI built-in interface will be used for API documentation and testing.")
    
    try:
        uvicorn.run(
            "api:app", 
            host=args.host, 
            port=args.port, 
            reload=args.reload,
            workers=args.workers,
            log_level=args.log_level
        )
        return 0
    except Exception as e:
        print(f"Error starting API server: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
