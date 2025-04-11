import os
import logging
from pathlib import Path
from .trellis_debug import debugger
import folder_paths

logger = logging.getLogger('ComfyUI-Trellis')

def normalize_path(path):
    return str(path).replace('\\', '/')

class TrellisModelLoaderNode:
    @classmethod
    def INPUT_TYPES(s):
        # Use both trellis_downloads and input/3d directories
        trellis_dir = os.path.join(folder_paths.get_output_directory(), "trellis_downloads")
        input_dir = os.path.join(folder_paths.get_input_directory(), "3d")
        
        # Create directories if they don't exist
        os.makedirs(trellis_dir, exist_ok=True)
        os.makedirs(input_dir, exist_ok=True)
        
        # Get files from both directories
        trellis_files = [normalize_path(os.path.join("trellis_downloads", f)) 
                        for f in os.listdir(trellis_dir) 
                        if f.endswith(('.gltf', '.glb'))]
        
        input_files = [normalize_path(os.path.join("3d", f)) 
                      for f in os.listdir(input_dir) 
                      if f.endswith(('.gltf', '.glb'))]
        
        all_files = sorted(trellis_files + input_files)
        
        return {"required": {
            "model_file": (all_files, {"file_upload": True}),
        }}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_path",)
    FUNCTION = "process_model"
    CATEGORY = "Trellis"
    
    def process_model(self, model_file):
        debugger.log_data("TrellisModelLoader", "Input", {
            "model_file": model_file
        })
        
        try:
            # Verify the file exists
            if model_file.startswith("trellis_downloads/"):
                base_path = Path(folder_paths.get_output_directory())
            else:
                base_path = Path(folder_paths.get_input_directory())
            
            full_path = base_path / model_file
            if not full_path.exists():
                raise FileNotFoundError(f"Model file not found: {full_path}")
            
            # Return normalized path
            model_path = normalize_path(str(full_path))
            debugger.log_data("TrellisModelLoader", "Output", {
                "model_path": model_path
            })
            
            return (model_path,)
            
        except Exception as e:
            debugger.log_data("TrellisModelLoader", "Error", str(e))
            logger.error(f"Error processing model: {e}")
            raise

class TrellisModelViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "model_path": ("STRING", {"default": ""})
        }}
    
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    FUNCTION = "process_model"
    CATEGORY = "Trellis"
    
    def process_model(self, model_path):
        debugger.log_data("TrellisModelViewer", "Input", {
            "model_path": model_path
        })
        
        try:
            # Ensure path is normalized
            model_path = normalize_path(model_path)
            
            return {
                "ui": {"model_path": model_path},
                "result": ()
            }
        except Exception as e:
            debugger.log_data("TrellisModelViewer", "Error", str(e))
            logger.error(f"Error in model viewer: {e}")
            raise

NODE_CLASS_MAPPINGS = {
    "TrellisModelLoader": TrellisModelLoaderNode,
    "TrellisModelViewer": TrellisModelViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisModelLoader": "Load 3D Model",
    "TrellisModelViewer": "View 3D Model"
} 