"""
Dashboard configuration module for CardioX ECG application.
This module provides configuration settings for the dashboard background and display options.
"""

def get_background_config():
    """
    Get the background configuration for the dashboard.
    
    Returns:
        dict: Configuration dictionary with background settings
    """
    return {
        "background": "none",
        "gif": False,
        "use_gif_background": False,
        "preferred_background": "none"
    }

def get_display_config():
    """
    Get the display configuration for the dashboard.
    
    Returns:
        dict: Configuration dictionary with display settings
    """
    return {
        "theme": "light",
        "medical_mode": False,
        "dark_mode": False,
        "responsive": True
    }

def get_asset_config():
    """
    Get the asset configuration for the dashboard.
    
    Returns:
        dict: Configuration dictionary with asset settings
    """
    return {
        "assets_path": "assets",
        "default_background": "solid",
        "fallback_images": ["her.png", "v.gif", "ECG1.png"]
    }
