import os
import json
import asyncio
import tempfile
import base64
import time
from PIL import Image
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TrellisAdvancedNodes')

# Import the base TrellisClientComfy from the main module
from .comfyui_trellis_node import TrellisClientComfy

class TrellisStatusNode:
    """Node that polls and displays the status of a Trellis processing task"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "session_id": ("STRING", {"default": ""}),
                "task_id": ("STRING", {"default": ""}),
                "server_url": ("STRING", {"default": "ws://18.199.134.45:46173"}),
                "poll_interval": ("FLOAT", {"default": 2.0, "min": 0.5, "max": 10.0, "step": 0.5}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "poll_status"
    CATEGORY = "Trellis"

    async def _poll_status_async(self, session_id, task_id, server_url, poll_interval):
        if not session_id or not task_id:
            return "Error: session_id and task_id are required"
        
        client = TrellisClientComfy(server_url)
        status = "initializing"
        
        try:
            await client.connect()
            
            # Define a websocket message to check status
            message = {
                'command': 'check_status',
                'session_id': session_id,
                'task_id': task_id
            }
            
            # Poll for status a few times
            for _ in range(5):  # Limit polling to 5 attempts
                await client.websocket.send(json.dumps(message))
                response = await client.websocket.recv()
                status_data = json.loads(response)
                
                status = status_data.get('status', 'unknown')
                logger.info(f"Status update: {status}")
                
                if status in ['complete', 'failed', 'error']:
                    break
                    
                await asyncio.sleep(poll_interval)
            
            await client.disconnect()
            return f"Status: {status}"
            
        except Exception as e:
            logger.error(f"Error polling status: {e}")
            if client.connected:
                await client.disconnect()
            return f"Error: {str(e)}"

    def poll_status(self, session_id, task_id, server_url, poll_interval):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            status = loop.run_until_complete(
                self._poll_status_async(session_id, task_id, server_url, poll_interval)
            )
            return (status,)
        finally:
            loop.close()


class TrellisSessionManager:
    """Node that manages Trellis sessions and provides session_id/task_id pairs"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "action": (["create", "load", "save"], {"default": "create"}),
                "session_name": ("STRING", {"default": "default_session"})
            },
            "optional": {
                "session_id": ("STRING", {"default": ""}),
                "task_id": ("STRING", {"default": ""})
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("session_id", "task_id")
    FUNCTION = "manage_session"
    CATEGORY = "Trellis"
    
    def __init__(self):
        self.sessions_dir = "trellis_sessions"
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    def manage_session(self, action, session_name, session_id="", task_id=""):
        if action == "create":
            # Generate a new session ID if none provided
            if not session_id:
                session_id = f"session_{int(time.time())}_{session_name}"
            if not task_id:
                task_id = f"task_{int(time.time())}"
                
            # Save the session
            self._save_session(session_name, session_id, task_id)
            return (session_id, task_id)
            
        elif action == "load":
            # Load an existing session
            loaded_session = self._load_session(session_name)
            if loaded_session:
                return (loaded_session["session_id"], loaded_session["task_id"])
            else:
                logger.warning(f"Session '{session_name}' not found, creating new one")
                return self.manage_session("create", session_name)
                
        elif action == "save":
            # Save the provided session
            if not session_id or not task_id:
                logger.error("Cannot save: session_id and task_id required")
                return ("", "")
                
            self._save_session(session_name, session_id, task_id)
            return (session_id, task_id)
            
        return ("", "")
        
    def _save_session(self, name, session_id, task_id):
        """Save session details to a file"""
        session_data = {
            "session_id": session_id,
            "task_id": task_id,
            "timestamp": time.time()
        }
        
        filename = os.path.join(self.sessions_dir, f"{name}.json")
        with open(filename, 'w') as f:
            json.dump(session_data, f)
            
        logger.info(f"Saved session '{name}' to {filename}")
        
    def _load_session(self, name):
        """Load session details from a file"""
        filename = os.path.join(self.sessions_dir, f"{name}.json")
        if not os.path.exists(filename):
            return None
            
        try:
            with open(filename, 'r') as f:
                session_data = json.load(f)
            logger.info(f"Loaded session '{name}' from {filename}")
            return session_data
        except Exception as e:
            logger.error(f"Error loading session '{name}': {e}")
            return None


class TrellisMultiImageNode:
    """Node that processes multiple images through Trellis WebSocket server"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "server_url": ("STRING", {"default": "ws://18.199.134.45:46173"}),
                "seed": ("INT", {"default": 1, "min": 1, "max": 2147483647}),
                "sparse_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "sparse_cfg_strength": ("FLOAT", {"default": 7.5, "min": 0.0, "max": 10.0, "step": 0.1}),
                "slat_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "slat_cfg_strength": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "simplify": ("FLOAT", {"default": 0.95, "min": 0.9, "max": 0.98, "step": 0.01}),
                "texture_size": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 512}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("glb_path", "video_path", "session_id", "task_id")
    FUNCTION = "process_multi"
    CATEGORY = "Trellis"

    async def _process_multi_async(self, images, server_url, seed, sparse_steps, sparse_cfg_strength, 
                           slat_steps, slat_cfg_strength, simplify, texture_size):
        # Setup parameters
        params = {
            'seed': seed,
            'sparse_steps': sparse_steps,
            'sparse_cfg_strength': sparse_cfg_strength,
            'slat_steps': slat_steps,
            'slat_cfg_strength': slat_cfg_strength,
            'simplify': simplify,
            'texture_size': texture_size
        }
        
        # Validate texture_size
        valid_texture_sizes = [512, 1024, 1536, 2048]
        if params['texture_size'] not in valid_texture_sizes:
            params['texture_size'] = min(valid_texture_sizes, key=lambda x: abs(x - params['texture_size']))
            logger.warning(f"Adjusted texture_size to {params['texture_size']}")
        
        # Convert all images to byte arrays
        image_bytes_list = []
        temp_files = []
        
        for i in range(len(images)):
            img = images[i]
            # Convert ComfyUI image to PIL
            pil_img = Image.fromarray((img * 255).astype(np.uint8))
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            pil_img.save(temp_file.name)
            temp_file.close()
            temp_files.append(temp_file.name)
            
            # Read as bytes
            with open(temp_file.name, 'rb') as f:
                image_bytes = f.read()
                image_bytes_list.append(image_bytes)
        
        # Process images using WebSocket
        client = TrellisClientComfy(server_url)
        
        try:
            # Connect to WebSocket
            if not await client.ensure_connection():
                raise ValueError("Could not establish connection to server")
                
            # Encode all images to base64
            encoded_images = [base64.b64encode(img_bytes).decode('utf-8') for img_bytes in image_bytes_list]
            
            # Prepare the WebSocket message
            message = {
                'command': 'process_multi',
                'images': encoded_images,
                'params': params
            }
            
            # Send the request
            await client.websocket.send(json.dumps(message))
            logger.info("Sent multi-image processing request")
            
            # Get initial response
            initial_response = await client.websocket.recv()
            initial_data = json.loads(initial_response)
            
            if initial_data.get('status') != 'accepted':
                raise ValueError(f"Request not accepted: {initial_data.get('message')}")
            
            task_id = initial_data.get('task_id')
            logger.info(f"Task accepted with ID: {task_id}")
            
            # Wait for processing completion
            while True:
                result = await client.websocket.recv()
                result_data = json.loads(result)
                
                if result_data.get('status') == 'success':
                    logger.info("Processing completed successfully")
                    session_id = result_data.get('session_id')
                    
                    # Download files
                    glb_path = await client.download_file(session_id, task_id, 'glb')
                    video_path = await client.download_file(session_id, task_id, 'video')
                    
                    await client.disconnect()
                    
                    # Clean up temp files
                    for file in temp_files:
                        os.unlink(file)
                        
                    return glb_path, video_path, session_id, task_id
                    
                elif result_data.get('status') == 'error':
                    raise ValueError(result_data.get('message', 'Processing failed'))
                    
        except Exception as e:
            logger.error(f"Error in process_multiple_images: {e}")
            if client.connected:
                await client.disconnect()
            
            # Clean up temp files
            for file in temp_files:
                if os.path.exists(file):
                    os.unlink(file)
                    
            return None, None, "", ""

    def process_multi(self, images, server_url, seed, sparse_steps, sparse_cfg_strength, 
                slat_steps, slat_cfg_strength, simplify, texture_size):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            glb_path, video_path, session_id, task_id = loop.run_until_complete(
                self._process_multi_async(images, server_url, seed, sparse_steps, sparse_cfg_strength, 
                                  slat_steps, slat_cfg_strength, simplify, texture_size)
            )
            return (glb_path or "", video_path or "", session_id or "", task_id or "")
        finally:
            loop.close()


class TrellisModelLoader:
    """Node that loads a 3D model file (GLB) for use in other nodes"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "glb_path": ("STRING", {"default": ""}),
            }
        }
    
    RETURN_TYPES = ("GLB_MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "load_model"
    CATEGORY = "Trellis"
    
    def load_model(self, glb_path):
        if not glb_path or not os.path.exists(glb_path):
            logger.error(f"GLB file not found: {glb_path}")
            return (None,)
            
        # Read the GLB file
        try:
            with open(glb_path, 'rb') as f:
                model_data = f.read()
                
            # Create a simple dict representation of the model
            # In a real implementation, this might use a 3D library to parse the GLB
            model = {
                "path": glb_path,
                "size": len(model_data),
                "type": "glb",
                "last_modified": os.path.getmtime(glb_path)
            }
            
            return (model,)
            
        except Exception as e:
            logger.error(f"Error loading GLB model: {e}")
            return (None,)


# Add these new node classes to the mappings
NODE_CLASS_MAPPINGS = {
    "TrellisStatusNode": TrellisStatusNode,
    "TrellisSessionManager": TrellisSessionManager,
    "TrellisMultiImageNode": TrellisMultiImageNode,
    "TrellisModelLoader": TrellisModelLoader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisStatusNode": "Trellis Status Monitor",
    "TrellisSessionManager": "Trellis Session Manager",
    "TrellisMultiImageNode": "Trellis Multi-Image Process",
    "TrellisModelLoader": "Trellis GLB Model Loader"
}
