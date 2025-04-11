import os
import logging
from pathlib import Path
from .trellis_debug import debugger
import folder_paths

logger = logging.getLogger('ComfyUI-Trellis')

def normalize_path(path):
    return str(path).replace('\\', '/')

class TrellisModelLoaderNode:
    SUPPORTED_FORMATS = ('.gltf', '.glb', '.obj', '.mtl', '.fbx', '.stl', '.usdz', '.dae')
    
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
                        if f.lower().endswith(s.SUPPORTED_FORMATS)]
        
        input_files = [normalize_path(os.path.join("3d", f)) 
                      for f in os.listdir(input_dir) 
                      if f.lower().endswith(s.SUPPORTED_FORMATS)]
        
        all_files = sorted(trellis_files + input_files)
        
        return {
            "required": {
                "model_file": (all_files, {
                    "file_upload": True,
                    "file_types": s.SUPPORTED_FORMATS,
                    "default": all_files[0] if all_files else ""
                }),
            },
            "optional": {
                "upload_to": (["input/3d", "trellis_downloads"], {"default": "input/3d"}),
                "convert_to_glb": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_path",)
    FUNCTION = "process_model"
    CATEGORY = "Trellis"
    
    def process_model(self, model_file, upload_to="input/3d", convert_to_glb=True):
        debugger.log_data("TrellisModelLoader", "Input", {
            "model_file": model_file,
            "upload_to": upload_to,
            "convert_to_glb": convert_to_glb
        })
        
        try:
            # Handle file upload if it's a new file
            if model_file.startswith("upload://"):
                file_path = model_file[9:]  # Remove "upload://" prefix
                filename = os.path.basename(file_path)
                
                # Determine target directory
                if upload_to == "input/3d":
                    target_dir = os.path.join(folder_paths.get_input_directory(), "3d")
                else:
                    target_dir = os.path.join(folder_paths.get_output_directory(), "trellis_downloads")
                
                # Create target directory if it doesn't exist
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy file to target location
                target_path = os.path.join(target_dir, filename)
                import shutil
                shutil.copy2(file_path, target_path)
                
                # Convert to GLB if needed
                if convert_to_glb and not filename.lower().endswith('.glb'):
                    try:
                        import trimesh
                        scene = trimesh.load(target_path)
                        glb_path = os.path.splitext(target_path)[0] + '.glb'
                        scene.export(glb_path)
                        target_path = glb_path
                        logger.info(f"Converted model to GLB: {glb_path}")
                    except ImportError:
                        logger.warning("trimesh not installed, skipping GLB conversion")
                    except Exception as e:
                        logger.error(f"Error converting to GLB: {e}")
                
                model_file = normalize_path(os.path.relpath(target_path, folder_paths.get_input_directory() if upload_to == "input/3d" else folder_paths.get_output_directory()))
            
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