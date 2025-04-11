"""
ComfyUI-Trellis
==============

This extension provides integration between ComfyUI and the Trellis 3D model generation system.
"""

import os
import sys
import shutil
from pathlib import Path
import logging
import importlib
from aiohttp import web  # Add this import

# Import debugger
try:
    from .nodes.trellis_debug import debugger
except ImportError:
    print("Could not import debugger. Debug logging will not be available.")
    debugger = None

# Import FastAPI app from ComfyUI
try:
    from server import PromptServer
    app = PromptServer.instance.app
except ImportError:
    print("Could not import PromptServer. Web endpoints will not be available.")
    app = None

# At the top after imports
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('ComfyUI-Trellis')

# Add file handler for persistent logging
fh = logging.FileHandler('comfyui_trellis.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

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

# Define base paths
BASE_DIR = Path(__file__).parent
COMFY_DIR = BASE_DIR.parent.parent  # Points to ComfyUI root
DOWNLOAD_DIR = BASE_DIR / "trellis_downloads"
COMFY_DOWNLOAD_DIR = COMFY_DIR / "trellis_downloads"  # Points to ComfyUI/trellis_downloads

# Use both directories for media paths
MEDIA_DIRS = [DOWNLOAD_DIR, COMFY_DOWNLOAD_DIR]

# Define all required directories
directories = [
    DOWNLOAD_DIR,
    BASE_DIR / "trellis_api_downloads",
    BASE_DIR / "trellis_sessions",
    BASE_DIR / "trellis_files" / "temp",
    BASE_DIR / "trellis_files" / "models",
    BASE_DIR / "trellis_files" / "videos",
    BASE_DIR / "trellis_metadata",
    BASE_DIR / "web"
]

# Create directories if they don't exist
for directory in directories:
    directory.mkdir(parents=True, exist_ok=True)

# Configure file serving - include both paths
MEDIA_PATHS = [str(path) for path in MEDIA_DIRS]

# Initialize node mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Dictionary of node modules to import
node_modules = {
    'nodes.trellis_media_nodes': 'media viewer nodes',
    'comfyui_trellis_node': 'basic Trellis WebSocket node',  # Keep this for WebSocket processing
}

# Import all node modules
for module_name, description in node_modules.items():
    try:
        module = importlib.import_module(f".{module_name}", package=__package__)
        if hasattr(module, 'NODE_CLASS_MAPPINGS'):
            NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
        if hasattr(module, 'NODE_DISPLAY_NAME_MAPPINGS'):
            NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)
        logger.info(f"Loaded {description}")
    except Exception as e:
        logger.error(f"Error loading {description}: {e}")

# Import and initialize web server components
try:
    from .webserver import server
    has_web_server = True
    logger.info("Web server components loaded successfully")
except ImportError:
    logger.warning("Web server components not loaded. Some features may not work correctly.")
    has_web_server = False

# Print startup information
print("=" * 80)
print(" ComfyUI-Trellis - 3D Model Generation Integration")
print("-" * 80)
print(" Available nodes:")
for node_name, display_name in NODE_DISPLAY_NAME_MAPPINGS.items():
    print(f" - {display_name}")
print("=" * 80)

logger.info(f"ComfyUI-Trellis loaded with {len(NODE_CLASS_MAPPINGS)} nodes")

WEB_DIRECTORY = BASE_DIR / "web"
# Add JavaScript dependencies
WEB_DEPENDENCIES = [
    "js/trellis-viewer.js"  # Only this JavaScript file
]

# Make sure files are loaded in correct order
def get_web_files():
    files = [str(WEB_DIRECTORY / file) for file in WEB_DEPENDENCIES]
    logger.debug(f"Loading web files: {files}")
    for file in files:
        if not Path(file).exists():
            logger.error(f"Web file not found: {file}")
    return files

# Web endpoint registration
def setup_web_endpoints():
    try:
        from server import PromptServer
        server = PromptServer.instance
        
        @server.routes.get("/trellis/check")
        async def check_trellis(request):
            logger.info("Trellis check endpoint called")
            return web.json_response({
                "status": "ok",
                "web_files": get_web_files(),
                "media_paths": MEDIA_PATHS
            })
            
        @server.routes.post("/trellis/debug")
        async def log_debug(request):
            try:
                data = await request.json()
                # Convert data to string if it's not serializable
                if isinstance(data.get('data'), (list, tuple)):
                    data['data'] = [str(x) for x in data['data']]
                
                if debugger:
                    debugger.log_data(
                        str(data.get('source', 'Unknown')),
                        'Frontend Log',
                        data.get('data', {})
                    )
                    return web.json_response({"status": "ok"})
                else:
                    logger.warning("Debug logging not available - debugger not initialized")
                    return web.json_response({"status": "warning", "message": "Debug logging not available"})
                    
            except Exception as e:
                logger.error(f"Error in debug endpoint: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return web.json_response({"status": "error", "message": str(e)}, status=500)
            
        @server.routes.get("/trellis/media-check/{filename:path}")
        async def check_media(request):
            filename = request.match_info['filename']
            logger.debug(f"Checking media accessibility for: {filename}")
            
            # Check both media directories
            for media_dir in MEDIA_DIRS:
                file_path = media_dir / filename
                if file_path.exists():
                    logger.debug(f"Found file at: {file_path}")
                    return web.json_response({
                        "exists": True,
                        "path": str(file_path),
                        "size": file_path.stat().st_size
                    })
            
            logger.warning(f"File not found: {filename}")
            return web.json_response({
                "exists": False,
                "searched": [str(d) for d in MEDIA_DIRS]
            })
            
        @server.routes.get("/trellis/view-video/{video_id}")
        async def view_video(request):
            video_id = request.match_info['video_id']
            logger.debug(f"Video viewer requested for: {video_id}")
            
            # Look for video file with this ID
            for media_dir in MEDIA_DIRS:
                for ext in ['.mp4', '.webm', '.mov']:
                    video_path = media_dir / f"{video_id}_output{ext}"
                    if video_path.exists():
                        logger.debug(f"Found video at: {video_path}")
                        return web.FileResponse(video_path)
            
            # If no video found, return 404
            logger.warning(f"No video found for ID: {video_id}")
            return web.Response(status=404, text="Video not found")

        @server.routes.get("/trellis/view-model/{model_id}")
        async def view_model(request):
            model_id = request.match_info['model_id']
            logger.debug(f"Model viewer requested for: {model_id}")
            
            # Look for model file with this ID
            for media_dir in MEDIA_DIRS:
                for ext in ['.glb', '.gltf']:
                    model_path = media_dir / f"{model_id}_output{ext}"
                    if model_path.exists():
                        logger.debug(f"Found model at: {model_path}")
                        return web.FileResponse(model_path)
            
            # If no model found, return 404
            logger.warning(f"No model found for ID: {model_id}")
            return web.Response(status=404, text="Model not found")

        logger.info("Trellis web endpoints registered successfully")
    except ImportError:
        logger.warning("Could not import PromptServer. Web endpoints will not be available.")
    except Exception as e:
        logger.error(f"Error setting up web endpoints: {e}")

# Call setup after everything else is initialized
setup_web_endpoints()


