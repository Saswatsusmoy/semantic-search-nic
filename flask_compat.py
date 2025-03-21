"""
Compatibility layer for transitioning from Flask to FastAPI
"""

from fastapi.templating import Jinja2Templates

def configure_templates(templates: Jinja2Templates):
    """
    Configure Jinja2 templates with Flask-compatible functions
    
    Args:
        templates: FastAPI Jinja2Templates object
    """
    
    # Define the Flask-compatible url_for function
    def url_for(name, **path_params):
        """
        Flask-compatible url_for function for templates
        
        Args:
            name: Route name (e.g. 'static')
            path_params: Path parameters including filename
        """
        if name == 'static':
            return f"/static/{path_params['filename']}"
        # For other routes, this would need to be expanded
        return f"/{name}"
    
    # Add the function to template globals
    templates.env.globals["url_for"] = url_for
    
    return templates
