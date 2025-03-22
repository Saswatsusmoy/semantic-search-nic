"""
Utility functions for API request/response handling and compatibility
"""

from typing import Dict, Any, Union, Optional
from fastapi import Form, Request
import json

async def parse_form_or_json(request: Request) -> Dict[str, Any]:
    """
    Parse either form data or JSON from a request
    
    Args:
        request: FastAPI request object
    
    Returns:
        Dict containing the parsed data
    """
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        # Parse JSON body
        try:
            return await request.json()
        except json.JSONDecodeError:
            return {}
    elif "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        # Parse form data
        form_data = await request.form()
        return {key: value for key, value in form_data.items()}
    
    # Default empty data
    return {}

def bool_form_field(value: Optional[str] = Form(None)) -> bool:
    """
    Convert string form field to boolean
    
    Args:
        value: Form field value
        
    Returns:
        Boolean representation of the value
    """
    if value is None:
        return False
    
    if isinstance(value, bool):
        return value
    
    return value.lower() in ("yes", "true", "t", "1", "on")
