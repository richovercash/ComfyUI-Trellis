import os
import json
import logging
from server import PromptServer

class TrellisInlineViewerNode:
    """Node that displays Trellis 3D models and videos directly in ComfyUI"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "file_path": ("STRING", {"default": ""}),
                "file_type": (["model", "video"], {"default": "model"}),
                "display_width": ("INT", {"default": 800, "min": 400, "max": 1920}),
                "display_height": ("INT", {"default": 600, "min": 300, "max": 1080}),
            }
        }
    
    RETURN_TYPES = ()
    FUNCTION = "display_content"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def display_content(self, file_path, file_type, display_width, display_height):
        if not file_path or not os.path.exists(file_path):
            return {"ui": {"error": f"File not found: {file_path}"}}
        
        # Create a unique ID for this viewer instance
        viewer_id = f"trellis_viewer_{hash(file_path) % 10000}"
        
        if file_type == "model":
            # Generate HTML for 3D model viewer
            html_content = self._generate_model_viewer(file_path, viewer_id, display_width, display_height)
        else:
            # Generate HTML for video player
            html_content = self._generate_video_player(file_path, viewer_id, display_width, display_height)
        
        # Return data to be displayed in ComfyUI
        return {"ui": {"viewer": {"type": file_type, "content": html_content, "viewer_id": viewer_id}}}
    
    def _generate_model_viewer(self, model_path, viewer_id, width, height):
        # Create an HTML viewer for Three.js
        # Convert backslashes to forward slashes for web use
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
        # Create an HTML5 video player
        html = f"""
        <div id="{viewer_id}" style="width:{width}px;height:{height}px;">
            <video width="{width}" height="{height}" controls autoplay>
                <source src="file://{web_path}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        </div>
        """
        return html

# Register a custom UI handler with ComfyUI
@PromptServer.instance.routes.get("/trellis/view/{viewer_id}")
async def get_trellis_viewer(request):
    viewer_id = request.match_info["viewer_id"]
    # Retrieve and serve viewer content
    return web.Response(text="Viewer content here", content_type="text/html")

# Add to node mappings
NODE_CLASS_MAPPINGS = {
    "TrellisInlineViewer": TrellisInlineViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisInlineViewer": "Trellis Inline Viewer"
}