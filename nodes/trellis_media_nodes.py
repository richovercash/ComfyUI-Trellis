import os
import server
from server import PromptServer

# nodes/trellis_media_nodes.py - Simplified version

# nodes/trellis_media_nodes.py - With output definitions

class TrellisModelViewerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_path": ("STRING", {"multiline": False}),
            }
        }
    
    # Define an output to connect to other nodes
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("model_path",)
    FUNCTION = "display_model"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True  # Mark as an output node (can be an endpoint)
    
    def display_model(self, model_path):
        # Pass through the model path both for UI and as output
        self.model_path = model_path  # Store for UI access
        return (model_path,)  # Return as tuple for node connections

class TrellisVideoPlayerNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "video_path": ("STRING", {"multiline": False}),
            }
        }
    
    # Define an output to connect to other nodes
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    FUNCTION = "play_video"
    CATEGORY = "Trellis"
    OUTPUT_NODE = True  # Mark as an output node (can be an endpoint)
    
    def play_video(self, video_path):
        # Pass through the video path both for UI and as output
        self.video_path = video_path  # Store for UI access
        return (video_path,)  # Return as tuple for node connections

# Node registration
NODE_CLASS_MAPPINGS = {
    "TrellisModelViewerNode": TrellisModelViewerNode,
    "TrellisVideoPlayerNode": TrellisVideoPlayerNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisModelViewerNode": "Trellis Model Viewer",
    "TrellisVideoPlayerNode": "Trellis Video Player"
}