import os
import json
import logging
from server import PromptServer

logger = logging.getLogger('TrellisInlineViewer')

class TrellisInlineViewerNode:
    """Node that displays Trellis 3D models and videos directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
                "file_type": (["auto", "model", "video"], {"default": "auto"}),
            },
            "optional": {
                "display_width": ("INT", {"default": 800, "min": 400, "max": 1920}),
                "display_height": ("INT", {"default": 600, "min": 300, "max": 1080}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "display_content"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def display_content(self, file_path, file_type="auto", display_width=800, display_height=600):
        try:
            if not file_path or not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return {"ui": {"error": f"File not found: {file_path}"}}
            
            # Determine file type if set to auto
            if file_type == "auto":
                extension = os.path.splitext(file_path)[1].lower()
                if extension in ['.glb', '.gltf']:
                    file_type = "model"
                elif extension in ['.mp4', '.webm', '.mov']:
                    file_type = "video"
                else:
                    logger.error(f"Unsupported file type: {extension}")
                    return {"ui": {"error": f"Unsupported file type: {extension}"}}
            
            # Create a unique ID for the viewer
            viewer_id = f"trellis_viewer_{hash(file_path) % 10000}"
            
            # Generate appropriate HTML
            if file_type == "model":
                html_content = self._generate_model_viewer(file_path, viewer_id, display_width, display_height)
            else:
                html_content = self._generate_video_player(file_path, viewer_id, display_width, display_height)
            
            # Return data to be displayed
            return {"ui": {"html": html_content}}
            
        except Exception as e:
            logger.error(f"Error in TrellisInlineViewerNode: {e}")
            return {"ui": {"error": str(e)}}
    
    def _generate_model_viewer(self, model_path, viewer_id, width, height):
        # Process the path before using it in the f-string
        web_path = os.path.abspath(model_path).replace('\\', '/')
        
        html = f"""
        <div id="{viewer_id}" style="width:{width}px;height:{height}px;"></div>
        <script>
            // Load Three.js and create viewer (simplified)
            const modelPath = "{web_path}";
            // Three.js initialization code here
        </script>
        """
        return html
    
    def _generate_video_player(self, video_path, viewer_id, width, height):
        # Process the path before using it in the f-string
        web_path = os.path.abspath(video_path).replace('\\', '/')
        
        html = f"""
        <div id="{viewer_id}" style="width:{width}px;height:{height}px;">
            <video width="{width}" height="{height}" controls autoplay>
                <source src="file://{web_path}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        """
        return html

# Add to node mappings
NODE_CLASS_MAPPINGS = {
    "TrellisInlineViewer": TrellisInlineViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisInlineViewer": "Trellis Inline Viewer"
}