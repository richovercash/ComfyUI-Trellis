"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
It allows using ComfyUI-generated images as input for Trellis processing to create 3D models.
"""

import os
import importlib.util
import sys
import logging

# Create main logger
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
dirs = ['trellis_downloads', 'trellis_files', 'trellis_files/viewers', 'trellis_files/players']

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)

# Import directly from the node file (simplifies imports)
try:
    from .comfyui_trellis_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    logger.info("Successfully imported Trellis nodes")
except ImportError as e:
    logger.error(f"Error importing Trellis nodes: {e}")
    # Provide empty mappings as fallback
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

# Add a note about the package to ComfyUI terminal
print("=" * 80)
print(" ComfyUI-Trellis - 3D Model Generation Integration")
print("-" * 80)
print(" Available nodes:")
for node_name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
    print(f" - {display_name}")
print("=" * 80)