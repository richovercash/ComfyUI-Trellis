"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
"""

import os
import sys
import logging
import importlib.util
from .comfyui_trellis_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ComfyUI-Trellis')

# Create directories
dirs = ['trellis_downloads', 'trellis_api_downloads', 'trellis_sessions', 
        'trellis_files', 'trellis_files/temp', 'trellis_files/models', 
        'trellis_files/viewers', 'trellis_files/players', 'trellis_files/videos', 'trellis_metadata']

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)

# Store node mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Load main nodes module
current_dir = os.path.dirname(os.path.abspath(__file__))

# Import the main processing node
try:
    from comfyui_trellis_node import NODE_CLASS_MAPPINGS as MAIN_NODE_MAPPINGS
    from comfyui_trellis_node import NODE_DISPLAY_NAME_MAPPINGS as MAIN_DISPLAY_MAPPINGS
    
    NODE_CLASS_MAPPINGS.update(MAIN_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(MAIN_DISPLAY_MAPPINGS)
    logger.info("Loaded main Trellis nodes")
except ImportError:
    # Try to import with the hyphenated filename
    try:
        spec = importlib.util.spec_from_file_location(
            "comfyui_trellis_node", 
            os.path.join(current_dir, "comfyui_trellis_node.py")
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
        NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
        logger.info("Loaded main Trellis nodes from hyphenated filename")
    except Exception as e:
        logger.error(f"Failed to import main Trellis nodes: {e}")

# Import the viewer node
try:
    # Try both possible filenames
    try:
        spec = importlib.util.spec_from_file_location(
            "trellis_viewer_node", 
            os.path.join(current_dir, "trellis_viewer_node.py")
        )
        if spec is None:
            spec = importlib.util.spec_from_file_location(
                "model_viewer_node", 
                os.path.join(current_dir, "model-viewer-node.py")
            )
        
        if spec:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
            NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
            logger.info("Loaded Trellis viewer nodes")
    except Exception as e:
        logger.error(f"Failed to import Trellis viewer nodes: {e}")
except:
    pass

# Report loaded nodes
logger.info(f"ComfyUI-Trellis loaded with {len(NODE_CLASS_MAPPINGS)} nodes:")
for node_name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
    logger.info(f"  - {display_name}")