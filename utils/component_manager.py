"""
Component Manager Utility Functions
"""

from flask import current_app

def get_component_manager():
    """Get component manager from current application"""
    return current_app.extensions['component_manager'] 