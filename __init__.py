"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
It allows using ComfyUI-generated images as input for Trellis processing to create 3D models.

Author: Your Name
Version: 0.1.0
"""

import os
import importlib.util
import sys

# Import node definitions
from .comfyui_trellis_node import NODE_CLASS_MAPPINGS as BASIC_NODE_CLASS_MAPPINGS
from .comfyui_trellis_node import NODE_DISPLAY_NAME_MAPPINGS as BASIC_NODE_DISPLAY_NAME_MAPPINGS

# # Import viewer node definitions
# from .trellis_viewer_node import NODE_CLASS_MAPPINGS as VIEWER_NODE_CLASS_MAPPINGS
# from .trellis_viewer_node import NODE_DISPLAY_NAME_MAPPINGS as VIEWER_NODE_DISPLAY_NAME_MAPPINGS


# Add these lines to your __init__.py
try:
    from .trellis_viewer_node import NODE_CLASS_MAPPINGS as VIEWER_NODE_MAPPINGS
    from .trellis_viewer_node import NODE_DISPLAY_NAME_MAPPINGS as VIEWER_NAME_MAPPINGS
    # Add viewer nodes to the mappings
    NODE_CLASS_MAPPINGS.update(VIEWER_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(VIEWER_NAME_MAPPINGS)
    print("Successfully loaded Trellis viewer nodes")
except Exception as e:
    print(f"Error loading Trellis viewer nodes: {e}")




# Import viewer node definitions
from .trellis_advanced_nodes import NODE_CLASS_MAPPINGS as VIEWER_NODE_CLASS_MAPPINGS
from .trellis_advanced_nodes import NODE_DISPLAY_NAME_MAPPINGS as VIEWER_NODE_DISPLAY_NAME_MAPPINGS

# Create main logger
import logging
logger = logging.getLogger('ComfyUI-Trellis')
logger.setLevel(logging.INFO)

# Check dependencies
required_packages = ['websockets', 'aiohttp', 'pillow']

missing_packages = []
for package in required_packages:
    spec = importlib.util.find_spec(package)
    if spec is None:
        missing_packages.append(package)

if missing_packages:
    logger.warning(f"Missing required packages: {', '.join(missing_packages)}")
    logger.warning("Please install them using: pip install " + " ".join(missing_packages))

# Ensure directories exist
dirs = ['trellis_downloads', 'trellis_api_downloads', 'trellis_sessions', 
        'trellis_files', 'trellis_files/temp', 'trellis_files/models', 
        'trellis_files/viewers', 'trellis_files/players', 'trellis_files/videos', 'trellis_metadata']

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)

# Create combined NODE_CLASS_MAPPINGS
NODE_CLASS_MAPPINGS = {**BASIC_NODE_CLASS_MAPPINGS, **VIEWER_NODE_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**BASIC_NODE_DISPLAY_NAME_MAPPINGS, **VIEWER_NODE_DISPLAY_NAME_MAPPINGS}

# Print startup message
logger.info(f"ComfyUI-Trellis loaded with {len(NODE_CLASS_MAPPINGS)} nodes")
for node_name in NODE_CLASS_MAPPINGS.keys():
    logger.info(f"  - {NODE_DISPLAY_NAME_MAPPINGS.get(node_name, node_name)}")

# Add a note about the package to ComfyUI terminal
print("=" * 80)
print(" ComfyUI-Trellis - 3D Model Generation Integration")
print("-" * 80)
print(" Available nodes:")
for node_name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
    print(f" - {display_name}")
print("=" * 80)



# Add to __init__.py
import folder_paths
from comfy.cli_args import args
import os

# Register HTML output type if needed
RETURN_TYPES = {
    "HTML": {"html": "HTML"}
}

# Register this if ComfyUI has a function for registering custom output types
# This is hypothetical - the exact method depends on ComfyUI's API
try:
    import comfy.utils
    comfy.utils.register_return_types(RETURN_TYPES)
except:
    print("Warning: Could not register HTML return type")

