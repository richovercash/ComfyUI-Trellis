import logging
from .trellis_debug import debugger
from pathlib import Path

logger = logging.getLogger('ComfyUI-Trellis')

def verify_media_path(path):
    """Verify that a media file exists and is accessible"""
    try:
        # Check if path is relative to trellis_downloads
        if path.startswith('trellis_downloads/'):
            # Check both possible locations
            base_paths = [
                Path(__file__).parent.parent,  # ComfyUI-Trellis/
                Path(__file__).parent.parent.parent.parent  # ComfyUI/
            ]
            
            for base in base_paths:
                full_path = base / path
                if full_path.exists():
                    logger.debug(f"Found media file at: {full_path}")
                    return str(full_path)
        
        # Try direct path
        direct_path = Path(path)
        if direct_path.exists():
            logger.debug(f"Found media file at direct path: {direct_path}")
            return str(direct_path)
        
        logger.warning(f"Media file not found: {path}")
        return None
    except Exception as e:
        logger.error(f"Error verifying media path: {e}")
        return None

class TrellisVideoPlayerNode:
    @classmethod
    def INPUT_TYPES(s):
        logger.debug("TrellisVideoPlayerNode: Initializing input types")
        return {
            "required": {
                "video_path": ("STRING", {"default": ""})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_video"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def process_video(self, video_path):
        debugger.log_data("VideoNode", "Input", {
            "path_type": str(type(video_path)),
            "path_value": video_path,
            "path_repr": repr(video_path)
        })
        
        try:
            video_path = str(video_path).strip()
            verified_path = verify_media_path(video_path)
            
            if not verified_path:
                logger.warning(f"Could not verify video path: {video_path}")
            
            debugger.log_data("VideoNode", "Path Verification", {
                "input_path": video_path,
                "verified_path": verified_path
            })
            
            return {
                "ui": {"video_path": verified_path or video_path},
                "result": (verified_path or video_path,)
            }
        except Exception as e:
            debugger.log_data("VideoNode", "Error", str(e))
            logger.error(f"TrellisVideoPlayerNode: Error processing video: {e}")
            raise

class TrellisModelViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_path": ("STRING", {"default": ""})
            }
        }
    
    RETURN_TYPES = ("STRING",)
    FUNCTION = "process_model"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True
    
    def process_model(self, model_path):
        debugger.log_data("ModelNode", "Input", {
            "path_type": str(type(model_path)),
            "path_value": model_path
        })
        
        logger.info(f"TrellisModelViewerNode: Processing model path: {model_path}")
        try:
            # Ensure we have a proper string
            if isinstance(model_path, (list, tuple)):
                model_path = ''.join(map(str, model_path))
            else:
                model_path = str(model_path)
                
            logger.debug(f"Processed model path: {model_path}")
            
            result = {
                "ui": {"model_path": model_path},
                "result": (model_path,)
            }
            debugger.log_data("ModelNode", "Output", result)
            return result
        except Exception as e:
            debugger.log_data("ModelNode", "Error", str(e))
            logger.error(f"TrellisModelViewerNode: Error processing model: {e}")
            raise

NODE_CLASS_MAPPINGS = {
    "TrellisVideoPlayerNode": TrellisVideoPlayerNode,
    "TrellisModelViewerNode": TrellisModelViewerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisVideoPlayerNode": "Trellis Video Player",
    "TrellisModelViewerNode": "Trellis Model Viewer"
} 