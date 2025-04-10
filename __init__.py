"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
"""

import os
import logging
import importlib.util


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
dirs = ['trellis_downloads', 'trellis_api_downloads', 'trellis_sessions', 
        'trellis_files', 'trellis_files/temp', 'trellis_files/models', 
        'trellis_files/videos', 'trellis_metadata']

for dir_path in dirs:
    os.makedirs(dir_path, exist_ok=True)

# Initialize empty mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Import and initialize web server components
# Import and initialize web server components
try:
    # This is the correct way to import from a subdirectory
    from .webserver import server
    has_web_server = True
except ImportError:
    logger.warning("Web server components not loaded. Some features may not work correctly.")
    has_web_server = False

# Define the web directory for ComfyUI to use for static file serving
WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")




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

if has_web_server:
    logger.info("Web server components loaded successfully")
else:
    logger.info("Web server components not loaded")


# Add this line near the end of the file, before the print statements
try:
    from . import webserver
    logger.info("Trellis web server loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Trellis web server: {e}")

import server

# Register our web routes
base_dir = os.path.dirname(os.path.realpath(__file__))
server.PromptServer.instance.app.router.add_static(
    "/trellis/static/",
    path=os.path.join(base_dir, "web"),
    name="trellis_static"
)
# # Print startup message
# logger.info(f"ComfyUI-Trellis loaded with {len(NODE_CLASS_MAPPINGS)} nodes")
# for node_name in NODE_CLASS_MAPPINGS.keys():
#     logger.info(f"  - {NODE_DISPLAY_NAME_MAPPINGS.get(node_name, node_name)}")

# Add a note about the package to ComfyUI terminal
print("=" * 80)
print(" ComfyUI-Trellis - 3D Model Generation Integration")
print("-" * 80)
print(" Available nodes:")
for node_name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
    print(f" - {display_name}")
print("=" * 80)



# # Add to __init__.py
# import folder_paths
# from comfy.cli_args import args
# import os

# # Register HTML output type if needed
# RETURN_TYPES = {
#     "HTML": {"html": "HTML"}
# }

# e
    # Add to your existing __init__.py

# # Import server components
# def init_webserver():
#     try:
#         from server import PromptServer
#         import webserver.server
#         print("Trellis Web Server initialized")
#     except Exception as e:
#         print(f"Error initializing Trellis Web Server: {e}")

# # Define web directory
# WEB_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), "web")

# # Initialize web server
# init_webserver()

