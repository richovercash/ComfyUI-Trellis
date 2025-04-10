"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
"""

import os
import logging

# Create main logger
logger = logging.getLogger('ComfyUI-Trellis')
logger.setLevel(logging.INFO)

# Ensure directories exist
dirs = ['trellis_downloads', 'trellis_api_downloads', 'trellis_sessions', 
        'trellis_files', 'trellis_files/temp', 'trellis_files/models', 
        'trellis_files/viewers', 'trellis_files/videos', 'trellis_metadata']

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)

# Initialize empty mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import node definitions one by one
try:
    from .comfyui_trellis_node import NODE_CLASS_MAPPINGS as BASIC_NODE_MAPPINGS
    from .comfyui_trellis_node import NODE_DISPLAY_NAME_MAPPINGS as BASIC_NAME_MAPPINGS
    NODE_CLASS_MAPPINGS.update(BASIC_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(BASIC_NAME_MAPPINGS)
    logger.info("Loaded basic Trellis nodes")
except Exception as e:
    logger.error(f"Error loading basic Trellis nodes: {e}")



# Import the simplified viewer node
try:
    from .basic_viewer import NODE_CLASS_MAPPINGS as VIEWER_MAPPINGS
    from .basic_viewer import NODE_DISPLAY_NAME_MAPPINGS as VIEWER_NAMES
    NODE_CLASS_MAPPINGS.update(VIEWER_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(VIEWER_NAMES)
    print("Successfully loaded simplified viewer node")
except Exception as e:
    print(f"Error loading simplified viewer: {e}")


# Import node definitions one by one
try:
    from .trellis_inline_node import NODE_CLASS_MAPPINGS as BASIC_NODE_MAPPINGS
    from .trellis_inline_node import NODE_DISPLAY_NAME_MAPPINGS as BASIC_NAME_MAPPINGS
    NODE_CLASS_MAPPINGS.update(BASIC_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(BASIC_NAME_MAPPINGS)
    logger.info("Loaded basic Trellis inline nodes")
except Exception as e:
    logger.error(f"Error loading basic Trellis inline nodes: {e}")


# Try to import advanced nodes if they exist
try:
    from .trellis_advanced_nodes import NODE_CLASS_MAPPINGS as ADVANCED_NODE_MAPPINGS
    from .trellis_advanced_nodes import NODE_DISPLAY_NAME_MAPPINGS as ADVANCED_NAME_MAPPINGS
    NODE_CLASS_MAPPINGS.update(ADVANCED_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(ADVANCED_NAME_MAPPINGS)
    logger.info("Loaded advanced Trellis nodes")
except Exception as e:
    logger.error(f"Error loading advanced Trellis nodes: {e}")

# Try to import viewer nodes if they exist
try:
    from .trellis_viewer_node import NODE_CLASS_MAPPINGS as VIEWER_NODE_MAPPINGS
    from .trellis_viewer_node import NODE_DISPLAY_NAME_MAPPINGS as VIEWER_NAME_MAPPINGS
    NODE_CLASS_MAPPINGS.update(VIEWER_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(VIEWER_NAME_MAPPINGS)
    logger.info("Successfully loaded Trellis viewer nodes")
except Exception as e:
    logger.error(f"Error loading Trellis viewer nodes: {e}")



# Try to import viewer nodes if they exist
try:
    from .trellis_preview_node import NODE_CLASS_MAPPINGS as VIEWER_NODE_MAPPINGS
    from .trellis_preview_node import NODE_DISPLAY_NAME_MAPPINGS as VIEWER_NAME_MAPPINGS
    NODE_CLASS_MAPPINGS.update(VIEWER_NODE_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(VIEWER_NAME_MAPPINGS)
    logger.info("Successfully loaded Trellis preview nodes")
except Exception as e:
    logger.error(f"Error loading Trellis preview nodes: {e}")

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

