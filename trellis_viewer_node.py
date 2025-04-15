import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger('TrellisViewer')

class TrellisModelViewerNode:
    """Node that renders a 3D model viewer directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "glb_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "background_color": (["#000000", "#222222", "#444444", "#FFFFFF"], {"default": "#222222"}),
                "auto_rotate": (["enabled", "disabled"], {"default": "enabled"}),
            }
        }
    
    RETURN_TYPES = ("OBJECT",)
    RETURN_NAMES = ("model_data",)
    FUNCTION = "process_model"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True  # Important for UI rendering!
    
    def process_model(self, glb_path, background_color="#222222", auto_rotate="enabled"):
        """Process 3D model for viewing"""
        if not glb_path or not os.path.exists(glb_path):
            return ({"error": "Model file not found"},)
            
        # Return data object that will be passed to the UI component
        return ({"path": glb_path, "background": background_color, "auto_rotate": auto_rotate == "enabled"},)
    


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
    """Node that renders a video player directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
            },
            "optional": {
                "autoplay": (["enabled", "disabled"], {"default": "disabled"}),
                "loop": (["enabled", "disabled"], {"default": "enabled"}),
            }
        }
    
    RETURN_TYPES = ("OBJECT",)
    RETURN_NAMES = ("video_data",)
    FUNCTION = "process_video"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True  # Important for UI rendering!
    
    def process_video(self, video_path, autoplay="disabled", loop="enabled"):
        """Process video path for playback"""
        if not video_path or not os.path.exists(video_path):
            return ({"error": "Video file not found"},)
            
        # Return data object that will be passed to the UI component
        return ({"path": video_path, "autoplay": autoplay == "enabled", "loop": loop == "enabled"},)


class TestVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "show_video"
    CATEGORY = "Test"
    OUTPUT_NODE = True
    
    def show_video(self, video_path):
        filename = os.path.basename(video_path)
        video_id = filename.replace('_output.mp4', '')
        
        return {
            "ui": {
                "iframe": f"/test-video/{video_id}"
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
    "TrellisVideoPlayerNode": TrellisVideoPlayerNode,
    "TrellisTestVideoNode": TestVideoNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisModelViewerNode": "Trellis 3D Model Viewer",
    "TrellisVideoPlayerNode": "Trellis Video Player",
    "TrellisTestVideoNode": "Trellis TestVideoNode"
}

