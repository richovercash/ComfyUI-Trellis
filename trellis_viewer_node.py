import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('TrellisViewer')



# class TrellisModelViewerNode:
#     @classmethod
#     def INPUT_TYPES(cls):
#         return {
#             "required": {
#                 "glb_path": ("STRING", {"default": ""}),
#             },
#             "optional": {
#                 "background_color": (["#000000", "#222222", "#444444", "#FFFFFF"], {"default": "#222222"}),
#             }
#         }
    
#     RETURN_TYPES = ()
#     FUNCTION = "view_model"
#     CATEGORY = "Trellis"
#     OUTPUT_NODE = True
    
#     def view_model(self, glb_path, background_color="#222222"):
#         if not glb_path or not os.path.exists(glb_path):
#             return {"ui": {"text": "Model file not found or invalid path"}}
        
#         session_id = os.path.basename(glb_path).replace('_output.glb', '')
        
#         # Return proper UI component definition for ComfyUI
#         return {
#             "ui": {
#                 "iframe": {
#                     "src": f"/trellis/view-model/{session_id}",
#                     "width": 800,
#                     "height": 600
#                 }
#             }
#         }
class TrellisModelViewerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "glb_path": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("glb_path",)
    FUNCTION = "view_model"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def view_model(self, glb_path):
        # Simply pass through the glb_path to make it available in onExecuted
        return (glb_path,)
    
    



class TrellisVideoPlayerNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "autoplay": (["enabled", "disabled"], {"default": "enabled"}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "view_video"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def view_video(self, video_path, autoplay="enabled"):
        if not video_path or not os.path.exists(video_path):
            return {"ui": {"text": "Video file not found or invalid path"}}
            
        session_id = os.path.basename(video_path).replace('_output.mp4', '')
        
        # Return embedded iframe
        return {
            "ui": {
                "iframe": {
                    "src": f"/trellis/view-video/{session_id}",
                    "width": 800,
                    "height": 600
                }
            }
        }


class TrellisViewNode:
    """Node that displays 3D models directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
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
        import hashlib
        file_hash = hashlib.md5(os.path.abspath(file_path).encode()).hexdigest()
        file_id = f"preview_{file_hash}"
        
        # Register file for serving
        from server import PromptServer
        if not hasattr(PromptServer.instance, 'trellis_files'):
            PromptServer.instance.trellis_files = {}
        
        PromptServer.instance.trellis_files[file_id] = {
            "path": os.path.abspath(file_path),
            "type": file_type,
            "mtime": os.path.getmtime(file_path)
        }
        
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



    


# Add these new node classes to the mappings
NODE_CLASS_MAPPINGS = {
    "TrellisModelViewerNode": TrellisModelViewerNode,
    "TrellisVideoPlayerNode": TrellisVideoPlayerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisModelViewerNode": "Trellis 3D Model Viewer",
    "TrellisVideoPlayerNode": "Trellis Video Player"
}
