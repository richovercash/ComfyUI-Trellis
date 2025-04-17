import json
import aiohttp
import os
import base64
import websockets
import asyncio
from PIL import Image
import io
import numpy as np
import tempfile
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('TrellisNode')

# Main Trellis Client for WebSocket communication
class TrellisClientComfy:
    def __init__(self, server_url, download_dir='trellis_downloads', output_subfolder='Otherrides_3d'):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        
        # Get path to ComfyUI outputs folder
        self.comfy_dir = self._find_comfy_root()
        self.outputs_dir = os.path.join(self.comfy_dir, 'output')
        
        # Create our specific subfolder within outputs
        self.output_subfolder = output_subfolder
        self.full_output_path = os.path.join(self.outputs_dir, self.output_subfolder)
        os.makedirs(self.full_output_path, exist_ok=True)
        
        # Keep old download dir for compatibility
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
        logger.info(f"ComfyUI outputs path: {self.outputs_dir}")
        logger.info(f"3D models will be saved to: {self.full_output_path}")

    def _find_comfy_root(self):
        """Find the ComfyUI root directory by traversing up from current file"""
        # Start with the directory containing this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Go up to find ComfyUI root (max 3 levels)
        for _ in range(3):
            # Check if this might be the ComfyUI root
            if os.path.isdir(os.path.join(current_dir, 'output')):
                return current_dir
            # Go up one level
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached root of filesystem
                break
            current_dir = parent_dir
        
        # Fallback - assume this is a ComfyUI extension in the custom_nodes directory
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    async def connect(self):
        """Connect to WebSocket server"""
        if self.websocket and not self.websocket.closed:
            logger.info("Already connected")
            return True

        try:
            # Ensure URL ends with /ws
            if not self.server_url.endswith('/ws'):
                url = f"{self.server_url.rstrip('/')}/ws"
            else:
                url = self.server_url
                
            logger.info(f"Connecting to {url}")
            
            # Simplified connection with fewer parameters
            self.websocket = await websockets.connect(url)
            
            self.connected = True
            logger.info("✓ Successfully connected to server")
            return True
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.connected = False
            self.websocket = None
            return False

    async def disconnect(self):
        if self.websocket:
            try:
                await self.websocket.close()
                self.websocket = None
                self.connected = False
                logger.info("✓ Disconnected from server")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")

    async def ensure_connection(self):
        """Ensure WebSocket connection is active"""
        if not self.connected or not self.websocket or self.websocket.closed:
            return await self.connect()
        return True

    async def process_image(self, image_data, params=None):
        """Process an image using WebSocket connection"""
        if not await self.ensure_connection():
            raise ValueError("Could not establish connection to server")

        try:
            # Convert image data to base64
            encoded_image = base64.b64encode(image_data).decode('utf-8')

            # Default parameters
            default_params = {
                'seed': 1,
                'sparse_steps': 12,
                'sparse_cfg_strength': 7.5,
                'slat_steps': 12,
                'slat_cfg_strength': 3,
                'simplify': 0.95,
                'texture_size': 1024
            }
            if params:
                default_params.update(params)

            # Prepare message
            message = {
                'command': 'process_single',
                'image': encoded_image,
                'params': default_params
            }

            # Send request
            await self.websocket.send(json.dumps(message))
            logger.info("Sent image processing request")

            # Get initial response
            initial_response = await self.websocket.recv()
            initial_data = json.loads(initial_response)

            if initial_data.get('status') != 'accepted':
                raise ValueError(f"Request not accepted: {initial_data.get('message')}")

            task_id = initial_data.get('task_id')
            logger.info(f"Task accepted with ID: {task_id}")

            # Wait for processing completion
            while True:
                result = await self.websocket.recv()
                result_data = json.loads(result)
                
                if result_data.get('status') == 'success':
                    return {
                        'task_id': task_id,
                        'session_id': result_data.get('session_id'),
                        'status': 'success'
                    }
                elif result_data.get('status') == 'error':
                    raise ValueError(result_data.get('message', 'Processing failed'))

        except Exception as e:
            logger.error(f"Error in process_image: {e}")
            self.connected = False  # Mark as disconnected on error
            raise

    async def download_file(self, session_id, task_id, file_type):
        """Download processed file (glb or video)"""
        try:
            # File extension based on type
            file_extension = 'mp4' if file_type == 'video' else 'glb'
            
            # Create unique filename based on session/task IDs
            filename = f"{session_id}_output.{file_extension}"
            
            # Path for ComfyUI outputs folder (for preview3d compatibility)
            output_path = os.path.join(self.full_output_path, filename)
            
            # Also save to original download dir for compatibility
            legacy_output_path = os.path.join(self.download_dir, filename)
            
            logger.info(f"➜ Downloading {file_type} file...")
            offset = 0
            chunks = []  # Store chunks temporarily
            
            # Collect chunks
            while True:
                command = f"get_{file_type}_chunk"
                request = {
                    'command': command,
                    'session_id': session_id,
                    'task_id': task_id,
                    'offset': offset,
                    'size': 50000  # 50KB chunks
                }
                
                await self.websocket.send(json.dumps(request))
                response = await self.websocket.recv()
                chunk_data = json.loads(response)
                
                if chunk_data.get('status') != 'success':
                    if chunk_data.get('message') == 'EOF':
                        break
                    raise ValueError(f"Server error: {chunk_data.get('message')}")
                
                chunk = base64.b64decode(chunk_data['data'])
                if not chunk:
                    break
                    
                chunks.append(chunk)
                offset += len(chunk)
            
            # Write all chunks to both file locations
            with open(output_path, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)
                    
            # Also write to legacy location for compatibility
            with open(legacy_output_path, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)

            logger.info(f"✓ Downloaded {file_type} file to {output_path}")
            
            # For compatibility with preview3d, return the relative path from ComfyUI output folder
            relative_path = os.path.join(self.output_subfolder, filename)
            return relative_path
                
        except Exception as e:
            logger.error(f"✗ Error downloading {file_type} file: {e}")
            return None


# ComfyUI Node Definitions
class TrellisProcessNode:
    """Node that processes an image through Trellis WebSocket server"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "server_url": ("STRING", {"default": "ws://35.164.116.189:38183"}),
                "seed": ("INT", {"default": 1, "min": 1, "max": 2147483647}),
                "sparse_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "sparse_cfg_strength": ("FLOAT", {"default": 7.5, "min": 0.0, "max": 10.0, "step": 0.1}),
                "slat_steps": ("INT", {"default": 12, "min": 1, "max": 50}),
                "slat_cfg_strength": ("FLOAT", {"default": 3.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "simplify": ("FLOAT", {"default": 0.95, "min": 0.9, "max": 0.98, "step": 0.01}),
                "texture_size": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 512}),
            },
            "optional": {
                "custom_output_dir": ("STRING", {"default": "Otherrides_3d"})
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("model_path", "video_path")
    FUNCTION = "process"
    CATEGORY = "Trellis"

    async def _process_async(self, image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                           slat_steps, slat_cfg_strength, simplify, texture_size, custom_output_dir=None):
        # Convert ComfyUI image format to bytes
        # Handle PyTorch tensor if present
        try:
            if hasattr(image[0], 'cpu'):
                # This is a PyTorch tensor, convert to numpy
                image_np = image[0].cpu().numpy()
            else:
                # Already a numpy array
                image_np = image[0]
                
            # Convert to PIL image
            image_pil = Image.fromarray((image_np * 255).astype(np.uint8))
            
            # Save to a temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            image_pil.save(temp_file.name)
            temp_file.close()
            
            # Read the file as bytes
            with open(temp_file.name, 'rb') as f:
                image_bytes = f.read()
            
            # Clean up the temporary file
            os.unlink(temp_file.name)
            
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
            
            # Validate texture_size to ensure it's one of the allowed values
            valid_texture_sizes = [512, 1024, 1536, 2048]
            if params['texture_size'] not in valid_texture_sizes:
                # Round to nearest valid size
                params['texture_size'] = min(valid_texture_sizes, key=lambda x: abs(x - params['texture_size']))
                logger.warning(f"Adjusted texture_size to {params['texture_size']}")
            
            # Use custom output dir if provided
            output_subfolder = custom_output_dir if custom_output_dir else "Otherrides_3d"
                
            # Process image
            client = TrellisClientComfy(server_url, output_subfolder=output_subfolder)
            
            try:
                result = await client.process_image(image_bytes, params)
                
                if not result or result.get('status') != 'success':
                    logger.error("Processing failed")
                    return None, None
                    
                # Download files
                model_path = await client.download_file(result['session_id'], result['task_id'], 'glb')
                video_path = await client.download_file(result['session_id'], result['task_id'], 'video')
                
                # Disconnect when done
                await client.disconnect()
                
                return model_path, video_path
            
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                if hasattr(client, 'connected') and client.connected:
                    await client.disconnect()
                return None, None
                
        except Exception as e:
            logger.error(f"Error preparing image: {e}")
            return None, None

    def process(self, image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                slat_steps, slat_cfg_strength, simplify, texture_size, custom_output_dir=None):
        # Create event loop and run async process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            model_path, video_path = loop.run_until_complete(
                self._process_async(image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                                  slat_steps, slat_cfg_strength, simplify, texture_size, custom_output_dir)
            )
            logger.info(f"Downloaded model file to: {model_path}")
            
            # Return relative path for preview3d compatibility
            return (model_path or "", video_path or "")
        finally:
            loop.close()


# Node Definitions
NODE_CLASS_MAPPINGS = {
    "TrellisProcessWebSocket": TrellisProcessNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisProcessWebSocket": "Trellis Process (WebSocket)"
}