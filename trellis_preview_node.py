import os
import json
import hashlib
import logging
from server import PromptServer
from aiohttp import web
from pathlib import Path

logger = logging.getLogger('TrellisPreview')

class TrellisPreview3DNode:
    """Node that previews 3D models directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "file_type": (["auto", "model", "video"], {"default": "auto"}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "preview_file"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def preview_file(self, file_path, file_type="auto"):
        if not file_path or not os.path.exists(file_path):
            return {"ui": {"status": "waiting"}}
        
        # Auto-detect file type if needed
        if file_type == "auto":
            ext = os.path.splitext(file_path)[1].lower()
            if ext in ['.glb', '.gltf']:
                file_type = "model"
            elif ext in ['.mp4', '.webm', '.mov']:
                file_type = "video"
            else:
                return {"ui": {"status": "error", "message": f"Unsupported file type: {ext}"}}
        
        # Generate a unique file ID based on file path
        file_hash = hashlib.md5(os.path.abspath(file_path).encode()).hexdigest()
        file_id = f"preview_{file_hash}"
        
        # Register file for serving
        if not hasattr(PromptServer.instance, 'trellis_files'):
            PromptServer.instance.trellis_files = {}
        
        PromptServer.instance.trellis_files[file_id] = {
            "path": os.path.abspath(file_path),
            "type": file_type,
            "mtime": os.path.getmtime(file_path)
        }
        
        logger.info(f"Registered file for preview: {file_path} (ID: {file_id})")
        
        # Return data for UI
        return {
            "ui": {
                "status": "ready",
                "preview": {
                    "file_id": file_id,
                    "file_type": file_type
                }
            }
        }
    
class TrellisModelViewerNode:
    """Node that previews 3D models directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "file_type": (["auto", "model", "video"], {"default": "auto"}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "preview_file"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True

    def UI(cls, glb_path):
        # Convert string path to Path object for safer handling
        path = Path(glb_path)
        
        # Log the path for debugging
        print(f"=== ModelNode - Output ===")
        print(json.dumps({
            "ui": {
                "model_path": str(path)
            },
            "result": [str(path)]
        }, indent=2))
        
        return {
            "ui": {
                "model_path": str(path)
            },
            "result": [str(path)]
        }
        
    def create_viewer(self, glb_path, background_color="#222222", display_width=800, 
                    display_height=600, auto_rotate="enabled", camera_distance=2.0):
        try:
            # Convert to Path object
            glb_path = Path(glb_path)
            
            # First try the path as-is
            if not glb_path.exists():
                # If it doesn't exist, try treating it as relative to COMFY_DIR
                from comfy.paths_internal import models_dir
                comfy_dir = Path(models_dir).parent
                alt_path = comfy_dir / glb_path
                
                if alt_path.exists():
                    glb_path = alt_path
                else:
                    logger.error(f"GLB file not found at either: {glb_path} or {alt_path}")
                    return self.create_error_html("Model file not found or invalid path"), ""
            
            # Create a unique viewer filename
            viewer_dir = Path("trellis_files") / "viewers"
            viewer_dir.mkdir(parents=True, exist_ok=True)
            
            viewer_filename = f"view_{glb_path.name.replace('_output.glb', '')}.html"
            viewer_path = viewer_dir / viewer_filename
        
                    # Configure viewer settings
            auto_rotate_value = "true" if auto_rotate == "enabled" else "false"
            
            # Create the HTML content with our modular JS viewer
            html_content = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trellis 3D Model Viewer</title>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; }}
            #viewer-container {{ width: 100%; height: 100vh; position: absolute; }}
        </style>
        
        <!-- Three.js and required addons -->
        <script src="https://unpkg.com/three@0.132.2/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.132.2/examples/js/controls/OrbitControls.js"></script>
        <script src="https://unpkg.com/three@0.132.2/examples/js/loaders/GLTFLoader.js"></script>
        <script src="https://unpkg.com/three@0.132.2/examples/js/loaders/DRACOLoader.js"></script>
        <script src="https://unpkg.com/three@0.132.2/examples/js/loaders/OBJLoader.js"></script>
        <script src="https://unpkg.com/three@0.132.2/examples/js/loaders/MTLLoader.js"></script>
        <script src="https://unpkg.com/three@0.132.2/examples/js/environments/RoomEnvironment.js"></script>
        
        <!-- Our custom viewer modules -->
        <script src="../web/js/ModelViewer.js"></script>
        <script src="../web/js/ModelLoader.js"></script>
        <script src="../web/js/ViewerUI.js"></script>
        <script src="../web/js/TrellisViewer.js"></script>
    </head>
    <body>
        <div id="viewer-container"></div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Initialize viewer
                var viewer = TrellisViewer.create({{
                    container: document.getElementById('viewer-container'),
                    viewer: {{
                        backgroundColor: parseInt('{background_color.replace("#", "0x")}'),
                        cameraPosition: [0, 1, {camera_distance}],
                        controlsAutoRotate: {auto_rotate_value}
                    }},
                    ui: {{
                        showControls: true,
                        showProgress: true,
                        showModelInfo: true,
                        theme: 'dark'
                    }}
                }});
                
                // Load the model
                viewer.loadModel('{relative_model_path}');
                
                // Handle window resize
                window.addEventListener('resize', function() {{
                    viewer.resize();
                }});
            }});
        </script>
    </body>
    </html>
    """
            
            # Write the HTML file
            with open(viewer_path, 'w') as f:
                f.write(html_content)
            
            logger.info(f"Created 3D viewer at: {viewer_path}")
            
            return html_content, viewer_path
            
        except Exception as e:
            logger.error(f"Error creating viewer: {e}")
            return self.create_error_html(str(e)), ""



# Add web routes
@PromptServer.instance.routes.get("/trellis/preview/files/{file_id}")
async def get_preview_file(request):
    """Serve the preview file"""
    file_id = request.match_info["file_id"]
    
    # Get the file info
    if not hasattr(PromptServer.instance, 'trellis_files'):
        return web.Response(status=404, text="File registry not found")
    
    file_info = PromptServer.instance.trellis_files.get(file_id)
    if not file_info:
        return web.Response(status=404, text="File not found")
    
    file_path = file_info["path"]
    if not os.path.exists(file_path):
        return web.Response(status=404, text="File no longer exists")
    
    # Determine content type
    content_type = "application/octet-stream"
    if file_info["type"] == "model":
        content_type = "model/gltf-binary"
    elif file_info["type"] == "video":
        content_type = "video/mp4"
    


# Register nodes
NODE_CLASS_MAPPINGS = {
    "TrellisPreview3D": TrellisPreview3DNode,
    "TrellisModelViewerNode": TrellisModelViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisPreview3D": "Trellis Preview 3D",
    "TrellisModelViewerNode": "Trellis Model Viewer"
}