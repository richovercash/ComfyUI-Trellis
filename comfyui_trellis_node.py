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
    def __init__(self, server_url, download_dir='trellis_downloads'):
        self.server_url = server_url
        self.websocket = None
        self.connected = False
        
        # Handle multiple possible download directories
        self.download_dir = self._get_download_dir(download_dir)
        logger.info(f"Using download directory: {self.download_dir}")

    def _get_download_dir(self, dir_name):
        """Get the best download directory path"""
        # First try: specified path
        if os.path.isabs(dir_name):
            os.makedirs(dir_name, exist_ok=True)
            return dir_name
            
        # Second try: subdirectory of current dir
        current_dir_path = os.path.join(os.getcwd(), dir_name)
        if os.path.exists(current_dir_path) or os.access(os.path.dirname(current_dir_path), os.W_OK):
            os.makedirs(current_dir_path, exist_ok=True)
            return current_dir_path
            
        # Third try: subdirectory of script dir
        script_dir = os.path.dirname(os.path.realpath(__file__))
        script_dir_path = os.path.join(script_dir, dir_name)
        os.makedirs(script_dir_path, exist_ok=True)
        return script_dir_path

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
            file_extension = 'mp4' if file_type == 'video' else 'glb'
            output_path = os.path.join(self.download_dir, f"{session_id}_output.{file_extension}")
            
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
            
            # Write all chunks to file
            with open(output_path, 'wb') as f:
                for chunk in chunks:
                    f.write(chunk)

            logger.info(f"✓ Downloaded {file_type} file to {output_path}")
            
            # Return just the ID part as a clean path for use in viewer nodes
            session_id_clean = session_id.strip()
            return session_id_clean
                
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
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("glb_path", "video_path")
    FUNCTION = "process"
    CATEGORY = "Trellis"

    async def _process_async(self, image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                           slat_steps, slat_cfg_strength, simplify, texture_size):
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
                
            # Process image
            client = TrellisClientComfy(server_url)
            
            try:
                result = await client.process_image(image_bytes, params)
                
                if not result or result.get('status') != 'success':
                    logger.error("Processing failed")
                    return None, None
                    
                # Download files
                glb_path = await client.download_file(result['session_id'], result['task_id'], 'glb')
                video_path = await client.download_file(result['session_id'], result['task_id'], 'video')
                
                # Disconnect when done
                await client.disconnect()
                
                return glb_path, video_path
            
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                if hasattr(client, 'connected') and client.connected:
                    await client.disconnect()
                return None, None
                
        except Exception as e:
            logger.error(f"Error preparing image: {e}")
            return None, None

    def process(self, image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                slat_steps, slat_cfg_strength, simplify, texture_size):
        # Create event loop and run async process
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            glb_path, video_path = loop.run_until_complete(
                self._process_async(image, server_url, seed, sparse_steps, sparse_cfg_strength, 
                                  slat_steps, slat_cfg_strength, simplify, texture_size)
            )
            logger.info(f"Downloaded GLB file path: {glb_path}")
            logger.info(f"Downloaded Video file path: {video_path}")
            return (glb_path or "", video_path or "")
        finally:
            loop.close()


# Node Definitions
NODE_CLASS_MAPPINGS = {
    "TrellisProcessWebSocket": TrellisProcessNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrellisProcessWebSocket": "Trellis Process (WebSocket)"
}