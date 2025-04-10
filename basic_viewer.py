import os
import logging

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
    FUNCTION = "create_viewer"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
# # Add to your basic_viewer.py
# def create_viewer(self, glb_path):
#     try:
#         # Log the original path
#         logger.info(f"Original GLB path: {glb_path}")
        
#         # Fix path format if needed
#         glb_path = os.path.abspath(glb_path)
#         logger.info(f"Absolute GLB path: {glb_path}")
        
#         # Check if file exists
#         if not os.path.exists(glb_path):
#             logger.error(f"GLB file not found: {glb_path}")
#             return "File not found"
            
#         # Try to read the file to verify permissions
#         try:
#             with open(glb_path, 'rb') as f:
#                 # Just read a small portion to verify access
#                 data = f.read(10)
#                 logger.info(f"Successfully read {len(data)} bytes from file")
#         except PermissionError:
#             logger.error(f"Permission denied when trying to read: {glb_path}")
#             return "Permission denied: " + glb_path
            
#         return glb_path
#     except Exception as e:
#         logger.error(f"Error in viewer: {e}")
#         return str(e)

def create_viewer(self, glb_path):
    try:
        if not glb_path or not os.path.exists(glb_path):
            logger.error(f"GLB file not found: {glb_path}")
            return "File not found"
        
        # Create a web-accessible copy
        import shutil
        import time
        
        # Create a model directory in ComfyUI's output folder (usually web-accessible)
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

