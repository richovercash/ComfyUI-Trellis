"""
Trellis Debug Viewer Node
========================

Simple debug node to test Three.js model viewer visibility in ComfyUI.
"""
import os
import json
import hashlib
import logging
from server import PromptServer
from aiohttp import web
from pathlib import Path

import logging

logger = logging.getLogger('ComfyUI-Trellis')

class TrellisDebugViewerNode:
    """Simple debug node to test container visibility and Three.js integration."""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "background_color": (["orange", "blue", "green", "red", "purple"], {"default": "orange"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_path",)
    FUNCTION = "debug_view"
    CATEGORY = "Trellis/Debug"
    
    def debug_view(self, model_path, background_color="orange"):
        """Simple pass-through function that logs model path."""
        logger.debug(f"Debug viewer node received model_path: {model_path}")
        logger.debug(f"Using background color: {background_color}")
        
        # Just return the path unchanged
        return (model_path,)

# Add to NODE_CLASS_MAPPINGS
NODE_CLASS_MAPPINGS = {
    "TrellisDebugViewerNode": TrellisDebugViewerNode,
}

# Add to NODE_DISPLAY_NAME_MAPPINGS
NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisDebugViewerNode": "Trellis Debug Viewer",
}