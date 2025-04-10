import os
import logging
import shutil
import time

logger = logging.getLogger('TrellisBasicViewer')

class TrellisSimpleViewerNode:
    """Basic viewer node for Trellis 3D models"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "glb_path": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("viewer_path",)
    FUNCTION = "process"  # This needs to match your actual method name
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    # Simple viewer    
    def process(self, glb_path):  # Method name must match FUNCTION value
        """Create a basic viewer for the 3D model"""
        try:
            logger.info(f"Processing GLB path: {glb_path}")
            
            if not glb_path or not os.path.exists(glb_path):
                logger.error(f"GLB file not found: {glb_path}")
                return "File not found"
            
            # Create a web-accessible copy
            web_dir = os.path.join("output", "trellis_models")
            os.makedirs(web_dir, exist_ok=True)
            
            # Create a unique filename
            filename = f"model_{int(time.time())}.glb"
            web_path = os.path.join(web_dir, filename)
            
            # Copy the file
            shutil.copy2(glb_path, web_path)
            logger.info(f"Copied model to web-accessible path: {web_path}")
            
            # Return the web path
            return web_path
        except Exception as e:
            logger.error(f"Error creating viewer: {e}")
            return str(e)

# Export node definitions
NODE_CLASS_MAPPINGS = {
    "TrellisSimpleViewerNode": TrellisSimpleViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisSimpleViewerNode": "Trellis Simple GLB Viewer"
}