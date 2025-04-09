"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
"""

import os
import logging

# Create main logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ComfyUI-Trellis')

# Ensure directories exist
os.makedirs('trellis_downloads', exist_ok=True)
os.makedirs('trellis_files', exist_ok=True)

# Import node mappings
from .comfyui_trellis_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

print("=" * 80)
print(" ComfyUI-Trellis - 3D Model Generation Integration")
print("-" * 80)
print(" Available nodes:")
for node_name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
    print(f" - {display_name}")
print("=" * 80)