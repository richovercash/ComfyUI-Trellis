import os
import json
import hashlib
import logging
from server import PromptServer
from aiohttp import web

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
    
    # Serve the file
    return web.FileResponse(file_path, headers={"Content-Type": content_type})

# Register nodes
NODE_CLASS_MAPPINGS = {
    "TrellisPreview3D": TrellisPreview3DNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisPreview3D": "Trellis Preview 3D"
}